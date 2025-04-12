import google.generativeai as genai
from fastapi import UploadFile
from dotenv import load_dotenv
import os

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
MODEL_NAME = "gemini-1.5-pro"  # or "gemini-pro-vision"

def get_description_from_image(file: UploadFile) -> str:
    model = genai.GenerativeModel(model_name=MODEL_NAME)

    image_bytes = file.file.read()  # read bytes directly from UploadFile

    response = model.generate_content(
        [
            "Describe this image in detail:",
            {"mime_type": file.content_type, "data": image_bytes}
        ]
    )

    return response.text