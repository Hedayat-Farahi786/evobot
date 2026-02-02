from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
import os

router = APIRouter(tags=["views"])

# Setup template engine
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
templates = Jinja2Templates(directory=os.path.join(base_dir, "templates"))

@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard page"""
    return templates.TemplateResponse("dashboard.html", {"request": request})

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Login page"""
    return templates.TemplateResponse("login.html", {"request": request})

@router.get("/test-realtime", response_class=HTMLResponse)
async def test_realtime(request: Request):
    """Real-time sync test page"""
    return templates.TemplateResponse("test_realtime.html", {"request": request})

@router.get("/assets/{folder}/{filename}")
async def serve_asset(folder: str, filename: str):
    """Serve static assets from assets folder"""
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    asset_path = os.path.join(base_dir, "assets", folder, filename)
    if os.path.exists(asset_path):
        return FileResponse(asset_path)
    raise HTTPException(status_code=404, detail="Asset not found")
