from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
import os

router = APIRouter(tags=["views"])

@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard page"""
    # Look for dashboard.html in templates (sibling to parent directory of this file)
    # current: dashboard/routers/views.py
    # templates: dashboard/templates/dashboard.html
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dashboard_path = os.path.join(base_dir, "templates", "dashboard.html")
    with open(dashboard_path, 'r', encoding='utf-8') as f:
        return f.read()

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Login page"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    login_path = os.path.join(base_dir, "templates", "login.html")
    with open(login_path, 'r', encoding='utf-8') as f:
        return f.read()

@router.get("/assets/{folder}/{filename}")
async def serve_asset(folder: str, filename: str):
    """Serve static assets from assets folder"""
    # dashboard/routers/views.py -> dashboard/routers -> dashboard -> root -> assets
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    asset_path = os.path.join(base_dir, "assets", folder, filename)
    if os.path.exists(asset_path):
        return FileResponse(asset_path)
    raise HTTPException(status_code=404, detail="Asset not found")
