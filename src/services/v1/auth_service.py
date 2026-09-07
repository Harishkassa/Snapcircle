from src.services.v1 import *

# internal imports
from src.core import (JWTManager)
from src.exception import (UserUnauthorizedException,
                           UserNotAuthenticated,
                           CustomBaseException,
                           DatabaseConnectionException)

from src.repository.user import UserRepository
from src.db import db, redisconnection

http_bearer = HTTPBearer(auto_error=False)

# FastAPI dependency: extracts and validates the bearer token, returns the authenticated user
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(http_bearer), db : Session = Depends(db.get_db)):
    try:
        token = credentials.credentials

        # Reject tokens that were explicitly logged out / blacklisted
        if await redisconnection.is_token_blacklisted(token):
            raise UserNotAuthenticated("Token Has Been Revoked, Not authenticated user")
    
        # Decode and validate JWT signature/expiry
        payload = JWTManager.verify_token(token=token)
    
        user_id = payload.get("id")

        # Token is valid but doesn't carry a user id — treat as unauthorized
        if user_id is None:
            raise UserUnauthorizedException("Unauthorized person can't access this")
    
        # Fetch the actual user record from DB using the id embedded in the token
        user_repository = UserRepository(db=db)
        user = await user_repository.get_by_id(user_id=user_id)
                    
        return user

    except CustomBaseException:
        # Re-raise known/expected exceptions as-is (already carry proper status/message)
        raise
    except Exception as e:
        # Wrap any unexpected error (e.g. DB failure) into a consistent exception type
        raise DatabaseConnectionException(f"Database error: {str(e)}")