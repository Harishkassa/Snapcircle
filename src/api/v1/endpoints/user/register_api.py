from src.api.v1.endpoints.user import *
from src.api.v1.router import router

# internal imports
from src.init import get_user_service
from src.core import JWTManager
from src.models import UserRegister
from src.services.v1 import UserService, get_current_user
from src.utils import limiter
from src.schemas.v1 import (
    UserCreate, 
    UserResponse, 
    UserUpdate,
    UpdateProfilePhoto
)

router = APIRouter()

# Registers a new user account
@router.post("/register", response_model=UserResponse, 
            response_description="Returns User Details",
            response_class=JSONResponse,
            response_model_exclude={"role_name", "profile_photo_id"},
            status_code=201)
@limiter.limit("5/minute")

async def register_user(
    request : Request, 
    create_user_data : UserCreate = Body(...),
    service : UserService = Depends(get_user_service)
):
    return await service.register_user(create_user_data)


# Updates the profile photo of the currently authenticated user
@router.put("/profile-photo")
async def update_profile_photo(
    update_user_data: UpdateProfilePhoto = Body(...),
    current_user: UserRegister = Depends(get_current_user),
    service: UserService = Depends(get_user_service)):

    # Only regular "User" role can update their own profile photo
    if current_user.role_name != "User":
        raise HTTPException(status_code=403, detail="Forbidden")
    
    await service.update_user_profile_photo(update_user_data=update_user_data, current_user=current_user)

    return {"status": "Successfully updated the user profile photo"}


# Returns a paginated list of all users
@router.get("/", response_model=List[UserResponse],
            response_description="Returns User Details",
            response_class=JSONResponse)

async def list_users(
    skip: int = Query(0, ge=0, description="Records skip"),
    limit: int = Query(100, le=500, description="Max records"),
    current_user: UserRegister = Depends(get_current_user),
    service: UserService = Depends(get_user_service),   # Closing add kiya
):
    # Restricted to "User" role only
    if current_user.role_name != "Admin":
        raise HTTPException(status_code=403, detail="Forbidden")

    return await service.get_all_users(skip=skip, limit=limit)


# Returns event photos where the given user's face was matched/detected
@router.get("/matched-photos/{user_id}")
async def get_matched_photos(
    user_id: UUID = Path(..., description="User's ID"),
    current_user: UserRegister = Depends(get_current_user),
    service: UserService = Depends(get_user_service), 
):
    
    if current_user.role_name != "User":
        raise HTTPException(status_code=403, detail="Forbidden")
    
    detected_faces = await service.get_matched_photos_for_user(user_id)
    # Reshape ORM objects into a lightweight response payload
    return [
        {
            "event_photo_id": df.event_photo_id,
            "photo_url": df.event_photos.photo_url,
            "detected_face_id": df.detected_face_id,
        }
        for df in detected_faces
    ]


# Returns details of a single user by ID (sensitive fields excluded from response)
@router.get("/{user_id}", response_model=UserResponse,
            response_description="Returns User Details",
            response_class=JSONResponse,
            response_model_exclude={"role_name", "profile_photo_id", "mobile_number"})

async def get_user(
    user_id : UUID = Path(..., description="User's ID"),
    current_user : UserRegister = Depends(get_current_user),
    service : UserService = Depends(get_user_service)
):
    
    if current_user.role_name != "User":
        raise HTTPException(status_code=403, detail="Forbidden")
    
    return await service.get_user(user_id)


# Updates a user's username
@router.put("/{user_id}",
            response_description="Update User Details",
            response_class=JSONResponse)

async def update_user(
    user_id : UUID = Path(..., description="User's ID"),
    user_update : UserUpdate = Depends(),
    service : UserService = Depends(get_user_service),
    current_user : UserRegister = Depends(get_current_user)
):
    
    if current_user.role_name != "User":
        raise HTTPException(status_code=403, detail="Forbidden")
    
    await service.update_user(user_id, user_update.new_username)

    return {"message" : f"User {current_user.user_id} is updated"}


# Deletes a user account by ID
@router.delete("/{user_id}",
            response_description="Delete User Details",
            response_class=JSONResponse)

async def delete_user(
    user_id : UUID = Path(..., description="User's ID"),
    service : UserService = Depends(get_user_service),
    current_user : UserRegister = Depends(get_current_user)
):
    
    if current_user.role_name != "User":
        raise HTTPException(status_code=403, detail="Forbidden")
    
    await service.delete_user(user_id=user_id)

    return {"message" : f"User {current_user.user_id} is deleted"}