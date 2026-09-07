from src.services.v1 import *

from src.services.v1.email_service import send_email_task
from src.services.v1.sms_service import send_sms_task

# internal imports
from src.repository.user import UserRepository

from src.core import (PasswordManager,
                      JWTManager, settings)

from src.models import UserRegister, ProfilePhoto

from src.exception import (UserNotFoundException,
                      DatabaseConnectionException,
                      FaceExpiredException,
                      UserAlreadyExistsException,
                      InvalidCredentialsException,
                      MissingRefreshToken,
                      InvalidRefreshToken,
                      ExpiredRefreshToken,
                      CustomBaseException
                      )
from src.db import redisconnection

from src.utils import GenerateOtp

logger = logging.getLogger(__name__)


class UserService:
 
    def __init__(self, user_repo: UserRepository, email_service: EmailService):
        self.repo          = user_repo
        self.email_service = email_service
    
    # Registers a new user: creates the DB record, then attaches their captured face
    # (pulled from Redis, cached earlier during the face-capture websocket flow) as profile photo
    async def register_user(self, create_user_data) -> "UserRegister":
    
        try:
            existing = await self.repo.get_by_email(create_user_data.email_id)
            if existing:
                raise UserAlreadyExistsException(f"User {create_user_data.email_id} already exists!")

            hashed_password = PasswordManager.hash(create_user_data.password)

            new_user = await self.repo.add_register_user(create_user_data, hashed_password)

            # Face was captured earlier via websocket and temporarily cached in Redis under this key
            redis_key = f"temp_face:{create_user_data.temp_face_id}"

            face_b64 = await redisconnection.get_value(redis_key)
            
            if not face_b64:
                logger.warning(f"Face capture expired or not found. Please capture again")
                raise HTTPException(
                    status_code=400,
                    detail="Face capture expired or not found. Please capture again."
                )

            # base64 -> bytes -> numpy image
            img_bytes = base64.b64decode(face_b64)

            upload_dir = "static"
            if not os.path.exists(upload_dir):
                os.makedirs(upload_dir)

            unique_filename = f"{create_user_data.username}.jpg"
            file_path = os.path.join(upload_dir, unique_filename)

            with open(file_path, "wb") as image_file:
                image_file.write(img_bytes)

            nparr = np.frombuffer(img_bytes, np.uint8)
            cropped_face_image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            embedding = await embedding_service.generate_embedding(cropped_face_image)

            if embedding is None:
                logger.warning(f"No face detected in cropped image for embedding")
                raise ValueError("No face detected in cropped image for embedding")

            new_profilephoto = await self.repo.add_profile_photo(
                                                    new_user, 
                                                    unique_filename, 
                                                    upload_dir, 
                                                    img_bytes, 
                                                    embedding
                                                    )

            logger.info(f"Profile Photo {new_profilephoto.photo_id} added")
            logger.info(f"User {new_user.user_id} created")

            return new_user
    
        except (CustomBaseException, HTTPException, ValueError):
            # Roll back DB changes and clean up any file already written to disk
            await self.repo.db.rollback()
            if 'file_path' in locals() and os.path.exists(file_path):
                os.remove(file_path)
            raise   
        except Exception as e:
            # catch-all for anything unexpected (redis error, cv2 failure, disk error, etc.)
            await self.repo.db.rollback()
            if 'file_path' in locals() and os.path.exists(file_path):
                os.remove(file_path)
            logger.error(f"Unexpected error in register_user: {str(e)}", exc_info=True)
            raise

    # Replaces an existing user's profile photo with a newly captured face
    async def update_user_profile_photo(self, update_user_data, current_user: UserRegister):
        try:
            redis_key = f"temp_face:{update_user_data.temp_face_id}"

            face_b64 = await redisconnection.get_value(redis_key)
            
            if not face_b64:
                raise FaceExpiredException()

            # base64 -> bytes -> numpy image
            img_bytes = base64.b64decode(face_b64)

            upload_dir = "static"
            if not os.path.exists(upload_dir):
                os.makedirs(upload_dir)

            unique_filename = f"{current_user.username}.jpg"
            file_path = os.path.join(upload_dir, unique_filename)

            with open(file_path, "wb") as image_file:
                image_file.write(img_bytes)

            nparr = np.frombuffer(img_bytes, np.uint8)
            cropped_face_image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            embedding = await embedding_service.generate_embedding(cropped_face_image)

            if embedding is None:
                logger.warning(f"No face detected in cropped image for embedding")
                raise ValueError("No face detected in cropped image for embedding")

            photo_url = f"/static/{unique_filename}"
            # Detect actual image format (jpeg/png/etc.) from the raw bytes rather than trusting the extension
            photo_type = Image.open(BytesIO(img_bytes)).format.lower()

            await self.repo.update_profile_photo(
                user_id=current_user.user_id,
                new_photo_url=photo_url,
                new_photo_type=photo_type,
                new_embedding=embedding,
            )

        except (CustomBaseException, ValueError):
            await self.repo.db.rollback()
            if 'file_path' in locals() and os.path.exists(file_path):
                os.remove(file_path)
            raise   
        except Exception as e:
            await self.repo.db.rollback()
            if 'file_path' in locals() and os.path.exists(file_path):
                os.remove(file_path)
            logger.error(f"Unexpected error in update_user_profile_photo: {str(e)}", exc_info=True)
            raise DatabaseConnectionException() from e
        
    async def get_user(self, user_id : UUID) -> "UserRegister":

        user = await self.repo.get_by_id(user_id)
        return user
    
    async def get_user_by_name(self, username : str) -> "UserRegister":

        user = await self.repo.get_user_by_name(username)
        return user
    
    async def get_user_by_email(self, email_id : str) -> "UserRegister":

        user = await self.repo.get_by_email(email_id)

        if user is None:
            logger.warning(f"No user found in table for this email {email_id}")
            raise UserNotFoundException()
        
        return user
    
    async def get_all_users(self, skip: int = 0, limit: int = 100) -> list["UserRegister"]:

        return await self.repo.get_all(skip=skip, limit=limit)
    
    async def update_user(self, user_id: int, new_username: str) -> "UserRegister":

        user = await self.repo.get_by_id(user_id)
        await self.repo.update_username(user, new_username=new_username)
            
    async def delete_user(self, user_id: int) -> None:

        user = await self.repo.get_by_id(user_id)
        await self.repo.delete_user(user=user)

    # Step 1 of email-based login: verify credentials, then generate + send OTP via email
    async def login_user_email_otp(self, email_id: str, password: str) -> None:

        user = await self.repo.get_by_email(email_id)
        if not user:
            logger.warning(f"No user found in table for this email {email_id}")
            raise UserNotFoundException(f"User {email_id} not found!")

        if not PasswordManager.verify(password, user.password):
            logger.warning(f"Password verification failed")
            raise InvalidCredentialsException("Invalid credentials")

        otp = GenerateOtp.generate_otp()
        await redisconnection.save_otp_with_rate_limit(email_id=email_id, new_otp=otp, channel="email")
        # Fire-and-forget: actual sending happens asynchronously via Celery worker
        send_email_task.delay(email_id=email_id, otp=otp)
        logger.info(f"OTP sent to user via email id")

    # Step 1 of mobile-based login: verify credentials, then generate + send OTP via SMS
    async def login_user_mobile_otp(self, email_id: str, password: str) -> None:

        user = await self.repo.get_by_email(email_id)
        if not user:
            logger.warning(f"No user found in table for this email {email_id}")
            raise UserNotFoundException(f"User {email_id} not found!")

        if not PasswordManager.verify(password, user.password):
            logger.warning(f"Password verification failed")
            raise InvalidCredentialsException("Invalid credentials")

        otp = GenerateOtp.generate_otp()
        await redisconnection.save_otp_with_rate_limit(email_id=user.email_id, new_otp=otp, channel="mobile")
        send_sms_task.delay(mobile_number=user.mobile_number, otp=otp)
        logger.info(f"OTP sent to user via SMS")

    # Resends a fresh OTP to the user's email (subject to cooldown inside save_otp_with_rate_limit)
    async def resend_otp_email(self, email_id: str) -> None:\
    
        user = await self.repo.get_by_email(email_id)
        if not user:
            logger.warning(f"No user found in table for this email {email_id}")
            raise UserNotFoundException(f"User {email_id} not found!")

        otp = GenerateOtp.generate_otp()
        logger.debug(f"otp {otp} resent via email")
        await redisconnection.save_otp_with_rate_limit(email_id=email_id, new_otp=otp, channel="email")  # 60 sec cooldown check
        send_email_task.delay(email_id=email_id, otp=otp)
        logger.info(f"OTP resent to user {email_id} via email")

    # Resends a fresh OTP to the user's mobile (subject to cooldown inside save_otp_with_rate_limit)
    async def resend_otp_mobile(self, email_id: str) -> None:

        user = await self.repo.get_by_email(email_id)
        if not user:
            logger.warning(f"No user found in table for this email {email_id}")
            raise UserNotFoundException(f"User {email_id} not found!")

        otp = GenerateOtp.generate_otp()
        logger.debug(f"otp {otp} resent via mobile")
        await redisconnection.save_otp_with_rate_limit(email_id=user.email_id, new_otp=otp, channel="mobile")  # 60 sec cooldown check
        send_sms_task.delay(mobile_number=user.mobile_number, otp=otp)
        logger.info(f"OTP resent to user {email_id} via SMS")
    
    # Final step of login: verifies OTP, then issues access token + sets refresh token cookie
    async def verify_otp_at_login(self, response, email_id: str, otp: str) -> str:
            
        user = await self.repo.get_by_email(email_id)
        if not user:
            logger.warning(f"No user found in table for this email {email_id}")   
            raise UserNotFoundException(f"User {email_id} not found!")

        if await redisconnection.otp_verification_by_email(email_id, otp):

            # Generate access token
            access_token = JWTManager.create_access_token(data={
                "sub": user.username,
                "role": user.role_name,
                "id": str(user.user_id),
                "email_id": user.email_id
            })

            # Issues a brand new refresh token family (fresh login session)
            raw_refresh = await self.repo.issue_refresh_token(user.user_id)

            self.set_refresh_cookie(response, raw_refresh)
            logger.info("Called set_refresh_cookie successfully")
            
            return access_token, user
        
    # Rotates the refresh token (reuse-detection included) and issues a new access token
    async def refresh(self, response : Response, refresh_token, old_access_token: Optional[str] = None)-> str:

        if not refresh_token:
            raise MissingRefreshToken()
        
        token_hash = JWTManager.hash_token(refresh_token)
        record = await self.repo.get_refresh_token_by_hash(token_hash=token_hash)
        
        if record.revoked:
            # --- REUSE DETECTION ---
            # This exact token was already rotated away once before.
            # Someone is replaying an old token => likely theft.
            # Kill every token in this family, forcing full re-login.
            await self.repo.revoke_token_family(family_id=record.family_id)
            raise HTTPException(401, "Refresh token reuse detected — all sessions revoked")
        
        if record.expires_at < datetime.now(timezone.utc):
            raise ExpiredRefreshToken()
    
        # Rotate: revoke old token, issue a new one in the same family
        record.revoked = True
    
        user = await self.repo.get_by_id(user_id=record.user_id)

        new_raw_refresh = await self.repo.issue_refresh_token(user_id=record.user_id, family_id=record.family_id)
        self.set_refresh_cookie(response, new_raw_refresh)
    
        new_access_token = JWTManager.create_access_token(data={
                "sub": user.username,
                "role": user.role_name,
                "id": str(user.user_id),
                "email_id": user.email_id
            })
        
        if old_access_token:
            await redisconnection.blacklisted_expire_token(old_access_token)

        return new_access_token, user


    # Logs the user out: blacklists their current access token and revokes the entire refresh token family
    async def log_out(self, response : Response,
                      token : Optional[str] = None, 
                      refresh_token: Optional[str] = None) -> str:
    
        await redisconnection.blacklisted_expire_token(token)

        if refresh_token:
            token_hash = JWTManager.hash_token(refresh_token)

            await self.repo.revoke_single_token(token_hash=token_hash)
        response.delete_cookie(settings.REFRESH_COOKIE_NAME, path="/api/v1/users/auth")

    # Initiates password reset by generating and emailing an OTP to the registered email
    async def forgot_password(self, email_id : str) -> str:
    
        user = await self.repo.get_by_email(email_id)
        if not user:
            logger.warning(f"No user found in table for this email {email_id}")    
            raise UserNotFoundException(f"User {email_id} not found!")
        
        # await self.repo.email_sending(user.email_id)
        otp = GenerateOtp.generate_otp()
        print("otp", otp)
        await redisconnection.save_otp_with_rate_limit(email_id=email_id, new_otp=otp)
        send_email_task.delay(email_id=email_id, otp=otp)
        logger.info(f"OTP sent to user {email_id} (email + sms)")
        

    # Completes password reset: verifies OTP, consumes it (single-use), then updates the password
    async def reset_password(self, email_id, otp, new_password) -> str:
            
        user = await self.repo.get_by_email(email_id)
        if not user:
            logger.warning(f"No user found in table for this email {email_id}")    
            raise UserNotFoundException(f"User {email_id} not found!")
        
        if await redisconnection.otp_verification_by_email(email_id, otp):
            
            # Hash the new password and update it in the database
            await self.repo.password_update(user, new_password)
        
    async def get_matched_photos_for_user(self, user_id : UUID):
        return await self.repo.get_matched_photos_for_user(user_id=user_id)
    
    # Sets the httpOnly refresh token cookie, scoped to /auth endpoints only
    def set_refresh_cookie(self, response: Response, raw_token: str):
        try:
            response.set_cookie(
                key=settings.REFRESH_COOKIE_NAME,
                value=raw_token,
                httponly=True,
                secure=False,        # HTTPS only — use False only for local http dev
                samesite="strict",  # or "lax" if you need cross-site navigation flows
                max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600,
                path="/api/v1/users/auth",        # scope the cookie to auth endpoints only
            )
        except Exception as e:
            raise HTTPException(status_code=410, detail=f"error occured {e}")