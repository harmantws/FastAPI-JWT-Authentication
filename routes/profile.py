from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request, Body, Form
from sqlalchemy.orm import Session
from models import Profile
from database import get_db
from schemas import *
import os, json
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from datetime import datetime
from fastapi.responses import FileResponse


router = APIRouter()
security = HTTPBearer()
UPLOAD_DIRECTORY = "uploaded_profile_images"
os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)


@router.get("/")
async def get_profile(request: Request, credentials: HTTPAuthorizationCredentials = Depends(security),db: Session = Depends(get_db)):
    user_id = request.state.user.get('user_id')
    profile = db.query(Profile).filter(Profile.user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    return {
        "id": profile.id,
        "user_id": profile.user_id,
        "bio": profile.bio,
        "location": profile.location,
        "birthdate": profile.birthdate,
        "image_url": profile.image_url,
    }

@router.post("/")
async def create_profile(request: Request,
                         bio: str = Form(...),
    location: str = Form(...),
    birthdate: date = Form(...),
    image:UploadFile=File(...),credentials: HTTPAuthorizationCredentials = Depends(security),db: Session = Depends(get_db)):

    user_id = request.state.user.get('user_id')
    print('User ID: %s' % user_id)
    profile_data = ProfileCreate(bio=bio, location=location, birthdate=birthdate)
    print("Profile_data-----", profile_data)
    existing_profile = db.query(Profile).filter(Profile.user_id == user_id).first()
    if existing_profile:
        raise HTTPException(
            status_code=400, detail="User already has a profile. Update it instead."
        )

    # Save image if provided
    image_url = None
    if image:
        unique_filename = f"{user_id}_{int(datetime.utcnow().timestamp())}_{image.filename}"
        file_location = os.path.join(UPLOAD_DIRECTORY, unique_filename)
        with open(file_location, "wb") as file:
            file.write(image.file.read())
        image_url = file_location
        print("Image saved--->", image_url)
    # Create new profile
    new_profile = Profile(
        user_id=user_id,
        bio=profile_data.bio,
        location=profile_data.location,
        birthdate=profile_data.birthdate,
        image_url=image_url,
    )
    db.add(new_profile)
    db.commit()
    db.refresh(new_profile)

    return {"message": "Profile created successfully", "data": new_profile.id}


@router.put("/")
async def update_profile(
    request: Request,
    bio: str = Form(None),
    location: str = Form(None),
    birthdate: date = Form(None),
    image: UploadFile = File(None),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    user_id = request.state.user.get("user_id")  # Fetch current user ID

    # Fetch the user's profile
    profile = db.query(Profile).filter(Profile.user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    # Update fields if provided
    if bio is not None:
        profile.bio = bio
    if location is not None:
        profile.location = location
    if birthdate is not None:
        profile.birthdate = birthdate

    # Handle image update
    if image:
        # Remove existing image if it exists
        if profile.image_url:
            try:
                os.remove(profile.image_url)
            except FileNotFoundError:
                pass  # Old image already missing; proceed
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error removing old image: {str(e)}")

        # Generate a unique filename using user ID and timestamp
        unique_filename = f"{user_id}_{int(datetime.utcnow().timestamp())}_{image.filename}"
        file_location = os.path.join(UPLOAD_DIRECTORY, unique_filename)

        # Save the new image
        with open(file_location, "wb") as file:
            file.write(image.file.read())
        profile.image_url = file_location

    db.commit()
    db.refresh(profile)

    return {"message": "Profile updated successfully", "data": profile.id}


@router.get('/download-image/')
async def download_image(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    user_id = request.state.user.get("user_id")

    # Fetch the user's profile
    profile = db.query(Profile).filter(Profile.user_id == user_id).first()
    if not profile or not profile.image_url:
        raise HTTPException(status_code=404, detail="Image not found")

    image_path = profile.image_url

    if not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail="Image file does not exist")
    extension = os.path.basename(image_path)
    extension = extension.split('.')[-1]
    # Serve the image file
    return FileResponse(
        path=image_path,
        media_type="application/octet-stream",
        filename=f"{request.state.user.get('username')}.{extension}"
    )