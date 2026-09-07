from src.api.v1.endpoints.user import *
from src.api.v1.router import router

# internal imports
from src.init import get_user_service
from src.services.v1 import UserService, http_bearer
from src.utils import limiter
from src.schemas.v1 import ( 
    LoginRequest, 
    LoginResponse,
    UserUpdatePassword,
    ResendOtpTemp
)
from src.core import settings


router = APIRouter()

# Step 1 of email-based login: verify credentials and trigger OTP email
@router.post("/auth/login/email-otp",
            response_description="Login User via email",
            response_class=JSONResponse)
@limiter.limit("5/minute")

async def login_email_otp(
    request : Request,
    user_login : LoginRequest = Body(...),
    service : UserService = Depends(get_user_service)
):
    # Validates identifier + password, then sends OTP via email
    await service.login_user_email_otp(user_login.identifier, user_login.password)

    return {"Message" : "OTP Email sent successfully"}


# Step 1 of mobile-based login: verify credentials and trigger OTP SMS
@router.post("/auth/login/mobile-otp",
            response_description="Login User via mobile",
            response_class=JSONResponse)
@limiter.limit("5/minute")

async def login_mobile_otp(
    request: Request,
    login_data: LoginRequest = Body(),
    service: UserService = Depends(get_user_service)
):
    # Validates identifier + password, then sends OTP via SMS
    await service.login_user_mobile_otp(email_id=login_data.identifier, password=login_data.password)

    return {"message": "OTP sent via SMS"}


# Resends a fresh OTP to the user's email (subject to cooldown handled in service layer)
@router.post("/auth/resend-otp/email",
             response_description="Resend Otp via email",
             response_class=JSONResponse)

async def resend_otp_email(
    resend_otp_data : ResendOtpTemp = Body(...),
    service : UserService = Depends(get_user_service)
):
    await service.resend_otp_email(email_id=resend_otp_data.email_id)

    return {"Message" : "OTP Email sent successfully"}


# Resends a fresh OTP to the user's mobile number (subject to cooldown handled in service layer)
@router.post("/auth/resend-otp/mobile",
             response_description="Resend Otp via mobile",
             response_class=JSONResponse)

async def resend_otp_mobile(
    resend_otp_data : ResendOtpTemp = Body(...),
    service: UserService = Depends(get_user_service)):
    await service.resend_otp_mobile(email_id=resend_otp_data.email_id)

    return {"message": "OTP resent via SMS"}


# Final step of login: verifies OTP and issues access + refresh tokens
@router.post("/auth/verify-otp",
            response_model=LoginResponse,
            response_description="Verify Otp",
            response_class=JSONResponse)
@limiter.limit("5/minute")

async def verify_otp(
    request : Request,
    response : Response, 
    otp_verification_data : OAuth2PasswordRequestForm = Depends(),
    service : UserService = Depends(get_user_service)
):
    
    # Generate access token
    # Sets refresh token cookie on `response` internally within the service call
    access_token, user = await service.verify_otp_at_login(response=response, email_id=otp_verification_data.username, otp=otp_verification_data.password)

    return LoginResponse(username=user.username,
                        role_name=user.role_name, 
                        access_token=access_token, 
                        token_type="bearer")    


# Rotates refresh token (read from cookie) and issues a new access token
@router.post("/auth/refresh",
            response_description="Verify Otp",
            response_model=LoginResponse)
        
async def refresh(
    response: Response,
    credentials : Optional[HTTPAuthorizationCredentials] = Depends(http_bearer),
    refresh_token: Optional[str] = Cookie(default=None, alias=settings.REFRESH_COOKIE_NAME),
    service : UserService = Depends(get_user_service)
):
    
    old_access_token = credentials.credentials if credentials else None
    
    new_access_token, user = await service.refresh(response, refresh_token, old_access_token)

    return LoginResponse(username=user.username,
                        role_name=user.role_name, 
                        access_token=new_access_token, 
                        token_type="bearer")   

# Logs the user out by blacklisting their access token (and revoking refresh token in service layer)
@router.post("/logout",
            response_description="Logout User",
            response_class=JSONResponse)

async def log_out_user(
    response : Response,
    credentials : HTTPAuthorizationCredentials = Depends(http_bearer),
    refresh_token: Optional[str] = Cookie(default=None, alias=settings.REFRESH_COOKIE_NAME),
    service : UserService = Depends(get_user_service)
):
    
    token = credentials.credentials if credentials else None
    await service.log_out(response, token, refresh_token)
    return {"Message": "Logged out Successfully"}


# Initiates password reset flow by sending an OTP to the user's registered email
@router.post("/forgot-password",
            operation_id="forgot_password",
            response_description="Forgot Password",
            response_class=JSONResponse)
@limiter.limit("5/minute")

async def forgot_password(
    request : Request,
    update_password_data : UserUpdatePassword = Body(...),
    service : UserService = Depends(get_user_service),
):
    
    await service.forgot_password(update_password_data.email_id)

    return "OTP Email sent successfully"


# Completes password reset by verifying OTP and setting the new password
@router.post("/reset-password",
            operation_id="reset_password",
            response_description="Reset Password",
            response_class=JSONResponse)
@limiter.limit("5/minute")

async def reset_password(
    request : Request,
    update_password_data : UserUpdatePassword = Body(...),
    service : UserService = Depends(get_user_service),
):
        
    await service.reset_password(email_id=update_password_data.email_id,
                                otp=update_password_data.otp, 
                                new_password=update_password_data.new_password)
   
    return {"Message": "Password reset successfully"}