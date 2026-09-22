"""
OnlyVeda Multilingual Nutraceutical Recommendation Chatbot
FastAPI Application Server & REST API
"""

import os
import sys
import shutil
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Ensure root directory is in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.config import SUPPORTED_LANGUAGES
from src.data_manager import ProductDataManager, DEFAULT_PRODUCTS_FILE
from src.bot_engine import OnlyVedaChatbot

app = FastAPI(title="OnlyVeda Nutraceutical Chatbot API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Core Services
data_manager = ProductDataManager()
chatbot = OnlyVedaChatbot(data_manager=data_manager)


# Pydantic Request Models
class ChatRequest(BaseModel):
    message: str
    language: Optional[str] = "en"
    session_id: Optional[str] = None


class ProductCreateRequest(BaseModel):
    name: str
    category: str
    key_ingredients: Any
    benefits: str
    dosage_and_usage: str
    health_concerns: Optional[Any] = None
    contraindications: Optional[str] = ""
    price_inr: Optional[float] = 0
    size: Optional[str] = ""
    image_url: Optional[str] = ""
    tags: Optional[Any] = None


class SettingsRequest(BaseModel):
    api_key: Optional[str] = ""


# Static Files setup
STATIC_DIR = os.path.join(BASE_DIR, "static")
os.makedirs(STATIC_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/logo.png")
async def get_logo():
    logo_path = os.path.join(STATIC_DIR, "logo.png")
    if not os.path.exists(logo_path):
        logo_path = os.path.join(BASE_DIR, "Onlyveda Logo.png")
    if os.path.exists(logo_path):
        return FileResponse(logo_path, media_type="image/png")
    raise HTTPException(status_code=404, detail="Logo not found")

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    template_path = os.path.join(BASE_DIR, "templates", "index.html")
    if os.path.exists(template_path):
        with open(template_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse("<h1>OnlyVeda Chatbot Backend Active</h1>")


@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    if not req.message or not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    result = chatbot.chat(
        user_message=req.message,
        selected_lang=req.language,
        session_id=req.session_id
    )
    return result


@app.get("/api/history/{session_id}")
async def get_session_history(session_id: str):
    """Retrieve full conversation history and active health context from persistent SQLite memory."""
    history = chatbot.memory.get_history(session_id, limit=50)
    context = chatbot.memory.get_session_context(session_id)
    return {
        "session_id": session_id,
        "history": history,
        "context": context
    }


@app.delete("/api/history/{session_id}")
async def clear_session_history(session_id: str):
    """Clear memory for a given session."""
    cleared = chatbot.memory.clear_session(session_id)
    return {
        "success": cleared,
        "session_id": session_id,
        "message": "Session history cleared" if cleared else "Session not found"
    }


@app.get("/api/sessions")
async def get_recent_sessions():
    """List recent consultation sessions."""
    sessions = chatbot.memory.get_all_sessions(limit=20)
    return {"sessions": sessions}


@app.get("/api/products")
async def get_products():
    return data_manager.get_all_products()


@app.post("/api/products")
async def add_product(prod: ProductCreateRequest):
    prod_dict = prod.model_dump()
    ok, msg = data_manager.add_product(prod_dict)
    if ok:
        chatbot.reload_data()
        return {"success": True, "message": msg}
    return {"success": False, "message": msg}


@app.post("/api/products/upload-csv")
async def upload_products_csv(file: UploadFile = File(...)):
    temp_path = os.path.join(BASE_DIR, "data", f"temp_upload_{file.filename}")
    os.makedirs(os.path.dirname(temp_path), exist_ok=True)
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        added, errors = data_manager.import_from_csv(temp_path)
        chatbot.reload_data()
        return {
            "success": True,
            "added": added,
            "errors": errors
        }
    except Exception as e:
        return {"success": False, "errors": [str(e)]}
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


@app.get("/api/products/export-csv")
async def export_products_csv():
    export_path = os.path.join(BASE_DIR, "data", "exported_products.csv")
    ok = data_manager.export_to_csv(export_path)
    if ok and os.path.exists(export_path):
        return FileResponse(export_path, filename="onlyveda_products.csv", media_type="text/csv")
    raise HTTPException(status_code=404, detail="No products to export")


@app.get("/data/products_template.csv")
async def download_template():
    template_path = os.path.join(BASE_DIR, "data", "products_template.csv")
    if os.path.exists(template_path):
        return FileResponse(template_path, filename="products_template.csv", media_type="text/csv")
    raise HTTPException(status_code=404, detail="Template not found")


@app.get("/api/languages")
async def get_languages():
    return SUPPORTED_LANGUAGES


@app.get("/api/status")
async def get_status():
    return {
        "status": "healthy",
        "product_count": len(data_manager.get_all_products()),
        "has_api_key": bool(chatbot.api_key),
        "supported_languages": list(SUPPORTED_LANGUAGES.keys())
    }


@app.post("/api/settings")
async def update_settings(settings: SettingsRequest):
    chatbot.set_api_key(settings.api_key)
    return {
        "success": True,
        "message": "API key updated successfully" if settings.api_key else "Using local Indic recommendation engine",
        "has_api_key": bool(chatbot.api_key)
    }


if __name__ == "__main__":
    import uvicorn
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app:app", host=host, port=port, reload=False)

