from src.repository.user import *

# internal imports
from src.models import UserRegister, ProfilePhoto, DetectedFace, RefreshToken
from src.exception import (UserNotFoundException,
                      UserAlreadyExistsException,
                      ProfilePhotoNotFound,
                      InvalidRefreshToken,
                      handle_db_errors
                      )
from src.core import PasswordManager

from src.db import db, redisconnection
from src.schemas.v1 import UserCreate
from src.core import settings, JWTManager

logger = logging.getLogger(__name__)



class UserRepository:

    def __init__(self, db: AsyncSession):
        self.db = db
    
    @handle_db_errors("add_register_user")
    async def add_register_user(self, create_user_data : UserCreate, hashed_password):

        try:        
            new_user = UserRegister(
                **create_user_data.model_dump(exclude={"password", "temp_face_id"}), 
                password=hashed_password
                )
            
            self.db.add(new_user)
            await self.db.flush()
            await self.db.refresh(new_user)

            logger.info(f"Registered user added into User table")  

            return new_user

        except IntegrityError as e:
            error_msg = str(e.orig).lower()
            logger.warning(error_msg)
            if "username" in error_msg:
                raise UserAlreadyExistsException("Username already exists!")
            elif "mobile_number" in error_msg:
                raise UserAlreadyExistsException("Mobile number already exists!")
            else:
                raise UserAlreadyExistsException("Duplicate entry detected!")


    @handle_db_errors("add_profile_photo")
    async def add_profile_photo(self, new_user : UserRegister, filename, upload_dir, img_bytes, embedding):
        
        new_profilephoto = ProfilePhoto(
            user_id=new_user.user_id,
            photo_url=f"/{upload_dir}/{filename}",
            photo_type=Image.open(BytesIO(img_bytes)).format.lower(),
            embedding=embedding
        )
        
        self.db.add(new_profilephoto)
        await self.db.flush()

        await self.db.refresh(new_user, attribute_names=["profile_photo"])

        logger.info(f"Profile Photo added into User table")  

        return new_profilephoto
    
    
    @handle_db_errors("get_by_id")
    async def get_by_id(self, user_id: UUID) -> "UserRegister":
        
        stmt = (select(UserRegister)
        .options(selectinload(UserRegister.profile_photo))
        .where(UserRegister.user_id == user_id)
        )
        
        user = (await self.db.scalars(stmt)).first()
            
        if not user:
            logger.warning(f"User {user_id} not found!")    
            raise UserNotFoundException(f"User {user_id} not found!")
        logger.info(f"User {user_id} fetched")
        return user
    
    @handle_db_errors("get_user_by_name")
    async def get_user_by_name(self, username: str) -> "UserRegister":

        stmt = select(UserRegister).where(UserRegister.username == username)
        user = (await self.db.scalars(stmt)).first()

        if not user:
            logger.warning(f"User {username} not found!")    
            raise UserNotFoundException(f"User {username} not found!")
        logger.info(f"User {user.username} fetched")
        return user
        
    @handle_db_errors("get_by_email")  
    async def get_by_email(self, email: str) -> Optional["UserRegister"]:

        stmt = select(UserRegister).where(UserRegister.email_id == email)
        user = (await self.db.scalars(stmt)).first()
            
        if not user:
            return None
        logger.info(f"User {email} fetched")
        return user
   
        
    @handle_db_errors("get_all")  
    async def get_all(self, skip: int = 0, limit: int = 100) -> list["UserRegister"]:
        
        stmt = (select(UserRegister)
        .options(selectinload(UserRegister.profile_photo))
        .offset(skip)
        .limit(limit)
        .order_by(UserRegister.updated_at.desc()))

        users =  list((await self.db.scalars(stmt)).all())
            
        return users
      
    @handle_db_errors("update_username")  
    async def update_username(self, user: UserRegister, new_username: str) -> "UserRegister":
        
        try:
            if new_username:
                user.username = new_username
            await self.db.flush()
            logger.info(f"Username of User {user.user_id} updated")
        except IntegrityError as e:
            error_msg = str(e.orig).lower()
            logger.warning(error_msg)
            if "username" in error_msg:
                raise UserAlreadyExistsException("Username already exists!")
        
    @handle_db_errors("delete_user")  
    async def delete_user(self, user: UserRegister):
        
        await self.db.delete(user)
        await self.db.flush()
        logger.info(f"User {user.user_id} Successfully deleted")
        
        
    @handle_db_errors("password_update")  
    async def password_update(self, user: "UserRegister", new_pwd: str):
            
        if not new_pwd:
            raise ValueError("New password not found")
        
        if new_pwd:
            user.password = PasswordManager.hash(new_pwd)
        await self.db.flush()
        logger.info("Password Successfully changed")
        

    @handle_db_errors("get_profile_photo_by_user_id")  
    async def get_profile_photo_by_user_id(self, user_id):
        stmt = select(ProfilePhoto).where(ProfilePhoto.user_id == user_id)
        result = (await self.db.scalars(stmt)).first()

        return result
    
    @handle_db_errors("update_profile_photo")  
    async def update_profile_photo(self, user_id, new_photo_url, new_photo_type, new_embedding):
        photo = await self.get_profile_photo_by_user_id(user_id)

        if photo is None:
            logger.warning(f"No profile photo found for user_id: {user_id}")    
            raise ProfilePhotoNotFound(f"No profile photo found for user_id: {user_id}")

        if new_photo_url:  
            photo.photo_url = new_photo_url
        
        if new_photo_type:
            photo.photo_type= new_photo_type
        
        if new_embedding:
            photo.embedding = new_embedding

        await self.db.flush()
        await self.db.refresh(photo)
        logger.info("Profile photo Successfully updated")

    @handle_db_errors("get_matched_photos_for_user")
    async def get_matched_photos_for_user(self, user_id: UUID):
        stmt = (
            select(DetectedFace)
            .options(selectinload(DetectedFace.event_photos))
            .where(DetectedFace.matched_user_id == user_id)
        )
        result = list((await self.db.scalars(stmt)).all())
        return result
   
    @handle_db_errors("issue_refresh_token")
    async def issue_refresh_token(self, user_id: UUID, family_id: Optional[UUID] = None) -> str:
        """Creates a new opaque refresh token, stores its hash, returns the raw token."""
        raw_token = secrets.token_urlsafe(64)
        logger.info(f"refresh raw token is: {raw_token}")
        record = RefreshToken(
            token_hash=JWTManager.hash_token(raw_token),
            user_id=user_id,
            family_id=family_id or secrets.token_hex(16),  # new family on login
            expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
            revoked=False,
        )
        self.db.add(record)
        await self.db.flush()
        return raw_token
    
    @handle_db_errors("get_refresh_token_by_hash")
    async def get_refresh_token_by_hash(self, token_hash: str):
        stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        result = await self.db.scalars(stmt)
        token = result.first()

        if not token:
            logger.warning("Refresh token not found or invalid")
            raise InvalidRefreshToken()

        return token
    
    @handle_db_errors("revoke_token_family")
    async def revoke_token_family(self, family_id: str):
        stmt = select(RefreshToken).where(RefreshToken.family_id == family_id)
        refresh_tokens = (await self.db.scalars(stmt)).all()   # sab tokens uthao

        for token in refresh_tokens:
            token.revoked = True

        await self.db.flush()
        logger.info("Refresh Token family revoked successfully")

    @handle_db_errors("revoke_single_token")
    async def revoke_single_token(self, token_hash):
        record = await self.get_refresh_token_by_hash(token_hash=token_hash)

        if token_hash:
            record.revoked = True

        await self.db.flush()
        await self.db.refresh(record)
        logger.info("single Refresh token raw revoked Successfully")

    @handle_db_errors("get_all_by_family")
    async def get_all_by_family(self, family_id: str):
        stmt = select(RefreshToken).where(RefreshToken.family_id == family_id)
        refresh_tokens = list((await self.db.scalars(stmt)).all())   # sab tokens uthao

        await self.db.flush()
        logger.info("Refresh Token family revoked successfully")

        return refresh_tokens