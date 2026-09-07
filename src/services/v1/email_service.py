from src.services.v1 import *

# internal imports
from src.core import settings
from src.exception import (EmailException,
                           EmailDeliveryException,
                           CustomBaseException)

logger = logging.getLogger(__name__)

# Celery app configured to use Redis as both message broker and result backend
celery_app = Celery(
    "tasks",
    broker=f"redis://:{settings.REDIS_PASSWORD}@cache:6379/0",
    backend=f"redis://:{settings.REDIS_PASSWORD}@cache:6379/0",
    include=["src.services.v1.multiple_face_embed_service"]
)

# Low-level helper: builds the OTP email message and sends it via SMTP
class EmailSender:  
    # Constructs a MIME email message containing the OTP code
    async def _build_otp_email(self, from_email: str, to_email: str, subject: str, otp: int):
        try:
            msg = MIMEMultipart()
            msg['from'] = from_email
            msg['to'] = to_email
            msg['subject'] = subject
            msg.attach(MIMEText(f"Your OTP Code is: {otp}", "plain"))
            logger.info(f"Email is ready to send for {to_email}")
            return msg
        except Exception as e:
            logger.error(f"Failed to build email: {str(e)}")
            raise EmailException(f"Failed to send email: {str(e)}")

    # Opens an SMTP connection, authenticates, and sends the built email
    async def _send_via_smtp(self, sender_email: str, sender_password: str, to_email: str, subject: str, otp: int):
        try:
            msg = await self._build_otp_email(sender_email, to_email, subject, otp)
            with smtplib.SMTP("smtp.gmail.com", 587) as server: 
                server.starttls()
                server.login(sender_email, sender_password)
                server.sendmail(sender_email, to_email, msg.as_string())
            logger.info(f"Email sent from {sender_email} to {to_email}")
            logger.info("Otp sent succesfuly")
        except CustomBaseException:
            # Already a known/handled exception type — propagate as-is
            raise
        except Exception as e:
            logger.error(f"SMTP connection failed: {str(e)}")
            raise EmailDeliveryException(f"Email sending connection failed: {str(e)}")

# Public-facing service used by callers (e.g. Celery task) to send an OTP email
class EmailService(EmailSender):
        async def _send_email(self, email_id: str, otp: str):
            sender_email = settings.EMAIL_HOST_USER
            sender_password = settings.EMAIL_HOST_PASSWORD

            # Fail fast if SMTP credentials aren't configured in environment
            if not sender_email or not sender_password:
                raise EmailException("Email credentials not loaded ❌")

            await self._send_via_smtp(sender_email, sender_password, email_id, "Your OTP Code", otp=otp)        

            return {
                "status" : "success"
            }

# Single shared instance used by the Celery task below
service = EmailService()

# isko class ke bahar assign karne ko bola standalone aisa kyu dekho puchh ke
# Celery task: retries automatically on failure (max 3x, exponential backoff), rate-limited to 15/min
@celery_app.task(
        autoretry_for=(Exception,),
        max_retries=3,
        retry_backoff=True,
        retry_backoff_max=10,
        rate_limit="15/m"
)
def send_email_task(email_id: str, otp: int):
    # Runs the async service method inside Celery's synchronous worker environment
    async_to_sync(service._send_email)(email_id=email_id, otp=otp)