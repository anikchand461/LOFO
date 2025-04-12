from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import traceback
from typing import List, Optional
from .models import User, Post
from .database import Base, engine, get_db
from .gemini_api import get_description_from_image
from .auth import create_user, authenticate_user
from . import schemas
from .routers import router as routers_router
import os
import shutil
from datetime import datetime

app = FastAPI(title="LOFO API", description="Lost and Found Online API")

# Create DB tables
Base.metadata.create_all(bind=engine)

# Create directories if they don't exist
os.makedirs("static", exist_ok=True)
os.makedirs("static/uploads", exist_ok=True)

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(routers_router, prefix="/api", tags=["posts"])

# Page routes
@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/login")
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/register")
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.get("/add-post")
async def add_post_page(request: Request):
    return templates.TemplateResponse("add-post.html", {"request": request})

@app.get("/profile")
async def profile_page(request: Request):
    return templates.TemplateResponse("profile.html", {"request": request})

# API routes
@app.post("/register", response_model=schemas.UserOut)
async def register(
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user_data = schemas.UserCreate(name=name, email=email, password=password)
    return create_user(user_data, db)

@app.post("/login", response_model=schemas.UserOut)
async def login(
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user_data = schemas.UserLogin(email=email, password=password)
    return authenticate_user(user_data, db)

@app.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    try:
        # Create a unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{file.filename}"
        file_path = f"static/uploads/{filename}"
        
        # Save the file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Get image description from Gemini API
        description = get_description_from_image(file)
        
        return {
            "filename": filename,
            "file_url": f"/static/uploads/{filename}",
            "description": description
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/posts", response_model=schemas.PostOut)
async def create_post(
    title: str = Form(...),
    type: str = Form(...),
    description: str = Form(...),
    location: str = Form(...),
    contact: str = Form(...),
    user_id: int = Form(...),
    image: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    try:
        image_url = None
        ai_description = None
        
        if image:
            # Create a unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{timestamp}_{image.filename}"
            file_path = f"static/uploads/{filename}"
            
            # Save the file
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(image.file, buffer)
            
            image_url = f"/static/uploads/{filename}"
            
            # For found items, get AI description
            if type == "found":
                try:
                    # Reset file pointer to beginning
                    await image.seek(0)
                    ai_description = get_description_from_image(image)
                except Exception as e:
                    print(f"Error getting AI description: {e}")
                    ai_description = None

        post = Post(
            title=title,
            type=type,
            description=ai_description if (type == "found" and ai_description) else description,
            location=location,
            contact=contact,
            user_id=user_id,
            image_url=image_url if type == "lost" else None  # Only store image URL for lost items
        )
        db.add(post)
        db.commit()
        db.refresh(post)
        return post
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/posts", response_model=List[schemas.PostOut])
async def get_posts(
    type: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Post)
    
    if type and type != 'all':
        query = query.filter(Post.type == type)
    
    if search:
        search = f"%{search}%"
        query = query.filter(
            (Post.title.ilike(search)) |
            (Post.description.ilike(search)) |
            (Post.location.ilike(search))
        )
    
    return query.all()

@app.get("/api/users/{user_id}/posts", response_model=List[schemas.PostOut])
async def get_user_posts(user_id: int, db: Session = Depends(get_db)):
    posts = db.query(Post).filter(Post.user_id == user_id).all()
    return posts

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)