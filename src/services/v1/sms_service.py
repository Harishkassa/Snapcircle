from src.services.v1 import *

# internal imports
from src.core import settings
from src.services.v1.email_service import celery_app  # same celery app/broker, ek hi worker sab tasks utha lega
from src.exception import (SMSException,
                           SMSDeliveryException,
                           CustomBaseException)

logger = logging.getLogger(__name__)

# Twilio error codes jo permanent hai - inpe retry karna faltu hai
NON_RETRYABLE_TWILIO_CODES = (21211, 21614, 21408, 21610, 21617)

twilio_client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)


# Low-level helper: builds the OTP SMS message and sends it via Twilio
class SmsSender:
    def _to_e164(self, mobile_number: str) -> str:
        # DB me plain 10 digit number save hai (valid_mobile check constraint), Twilio ko +country_code chahiye
        if mobile_number.startswith("+"):
            return mobile_number
        return f"{settings.DEFAULT_COUNTRY_CODE}{mobile_number}"

    # Constructs the OTP message text
    async def _build_otp_message(self, otp: str) -> str:
        try:
            message = f"Your OTP code is: {otp}. Valid for 5 minutes. Do not share this with anyone."
            logger.info("SMS message is ready to send")
            return message
        except Exception as e:
            logger.error(f"Failed to build sms message: {str(e)}")
            raise SMSException(f"Failed to send sms: {str(e)}")

    # Sends the OTP SMS through Twilio, converting number to E.164 format first
    async def _send_via_twilio(self, mobile_number: str, otp: str):
        try:
            body = await self._build_otp_message(otp)
            to_number = self._to_e164(mobile_number)

            sms = twilio_client.messages.create(
                body=body,
                from_=settings.TWILIO_PHONE_NUMBER,
                to=to_number,
            )
            logger.info(f"SMS sent to {to_number}, sid: {sms.sid}, status: {sms.status}")
            return sms

        except CustomBaseException:
            # Already a known/handled exception type — propagate as-is
            raise
        except TwilioRestException as e:
            logger.error(f"Twilio connection failed: {str(e)}")
            if e.code in NON_RETRYABLE_TWILIO_CODES:
                # invalid/unreachable number - retry karne se koi fayda nahi
                # Non-retryable: raise plain SMSException so Celery's autoretry doesn't kick in
                raise SMSException(f"SMS could not be delivered: {e.msg}")
            # Transient Twilio failure — raise SMSDeliveryException so Celery retries
            raise SMSDeliveryException(f"SMS sending connection failed: {str(e)}")
        except Exception as e:
            logger.error(f"SMS connection failed: {str(e)}")
            raise SMSDeliveryException(f"SMS sending connection failed: {str(e)}")


# Public-facing service used by callers (e.g. Celery task) to send an OTP SMS
class SMSService(SmsSender):
    async def _send_sms(self, mobile_number: str, otp: str):
        # Fail fast if Twilio credentials aren't configured in environment
        if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN:
            raise SMSException("Twilio credentials not loaded ❌")

        await self._send_via_twilio(mobile_number, otp=otp)

        return {
            "status": "success"
        }

# Single shared instance used by the Celery task below
service = SMSService()

# Celery task: retries only on transient failures (not invalid numbers), rate-limited to 15/min
@celery_app.task(
        autoretry_for=(SMSDeliveryException,),
        max_retries=3,
        retry_backoff=True,
        retry_backoff_max=10,
        rate_limit="15/m"
)
def send_sms_task(mobile_number: str, otp: str):
    # Runs the async service method inside Celery's synchronous worker environment
    async_to_sync(service._send_sms)(mobile_number=mobile_number, otp=otp)