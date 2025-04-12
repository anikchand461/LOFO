import os
from fastapi import APIRouter, UploadFile, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from .gemini_api import get_description_from_image
from .matcher import get_best_match  # Adjusted to match your earlier matcher function name
from .database import get_db
from .models import Post, User
from .schemas import PostCreate, PostOut
from datetime import datetime

UPLOAD_FOLDER = "backend/uploads"
router = APIRouter()

# Dependency to get the current user (simplified; replace with JWT later)
def get_current_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid user")
    return user

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@router.post("/upload")
async def upload_image(
    file: UploadFile,
    user_id: int,
    item_type: str,  # 'lost' or 'found' passed as query parameter
    location: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if item_type not in ["lost", "found"]:
        raise HTTPException(status_code=400, detail="Item type must be 'lost' or 'found'")

    # Save the uploaded file
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    # Step 1: Get AI-generated description from Gemini
    description = get_description_from_image(file_path)

    # Step 2: Fetch all relevant posts from the database (e.g., lost items if found, or vice versa)
    if item_type == "found":
        owner_entries = db.query(Post).filter(Post.type == "lost").all()
    else:  # lost
        owner_entries = db.query(Post).filter(Post.type == "found").all()

    # Convert DB rows to a list of dicts for matching (adjusting to match_description format)
    owner_reports = [{"name": str(o.id), "description": o.description} for o in owner_entries]

    # Step 3: Use matcher to find best match
    best_match = get_best_match(description, owner_reports) if owner_reports else {"error": "No matches found"}

    # Step 4: Save the new post to the database
    db_post = Post(
        user_id=user_id,
        type=item_type,
        description=description,
        location=location,
        time=str(datetime.now())
    )
    db.add(db_post)
    db.commit()
    db.refresh(db_post)

    return JSONResponse(
        content={
            "gemini_description": description,
            "matched_owner": best_match,
            "new_post_id": db_post.id
        },
        status_code=201
    )

@router.get("/posts/{user_id}", response_model=list[PostOut])
def get_user_posts(user_id: int, db: Session = Depends(get_db)):
    posts = db.query(Post).filter(Post.user_id == user_id).all()
    return posts