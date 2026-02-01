from fastapi import APIRouter, Request
from typing import Dict, Any
from datetime import datetime
from core.security import security_manager

router = APIRouter(prefix="/api/settings", tags=["settings"])

@router.get("")
async def get_all_settings():
    """Get all settings from Firebase (public read, masked sensitive data)"""
    from core.firebase_settings import firebase_settings
    settings = firebase_settings.get_all()
    
    # Mask sensitive data
    if 'telegram' in settings:
        if settings['telegram'].get('api_hash'):
            settings['telegram']['api_hash'] = '***masked***'
    if 'broker' in settings:
        if settings['broker'].get('metaapi_token'):
            settings['broker']['metaapi_token'] = '***masked***'
        if settings['broker'].get('password'):
            settings['broker']['password'] = '***masked***'
    
    return settings

@router.get("/{section}")
async def get_settings_section(section: str):
    """Get settings for a specific section"""
    from core.firebase_settings import firebase_settings
    settings = firebase_settings.get_section(section)
    
    # Mask sensitive data
    if section == 'telegram' and settings.get('api_hash'):
        settings['api_hash'] = '***masked***'
    if section == 'broker':
        if settings.get('metaapi_token'):
            settings['metaapi_token'] = '***masked***'
        if settings.get('password'):
            settings['password'] = '***masked***'
    
    return {
        "section": section,
        "settings": settings,
        "timestamp": datetime.utcnow().isoformat()
    }

@router.put("")
async def update_all_settings(settings: Dict[str, Any]):
    """Update all settings at once"""
    from core.firebase_settings import firebase_settings
    firebase_settings.update_all(settings)
    
    security_manager.audit_log(
        "settings_updated",
        "dashboard",
        details={"sections": list(settings.keys())},
        severity="info"
    )
    
    return {"status": "success", "message": "All settings updated"}

@router.put("/{section}")
async def update_settings_section(section: str, values: Dict[str, Any]):
    """Update settings for a specific section"""
    from core.firebase_settings import firebase_settings
    firebase_settings.set_section(section, values)
    
    security_manager.audit_log(
        "settings_updated",
        "dashboard",
        details={"section": section},
        severity="info"
    )
    
    return {"status": "success", "message": f"Settings for {section} updated"}

@router.put("/{section}/{key}")
async def update_single_setting(section: str, key: str, request: Request):
    """Update a single setting value"""
    from core.firebase_settings import firebase_settings
    body = await request.json()
    value = body.get("value")
    
    firebase_settings.set(section, key, value)
    
    security_manager.audit_log(
        "setting_updated",
        "dashboard",
        details={"section": section, "key": key},
        severity="info"
    )
    
    return {"status": "success", "message": f"Setting {section}.{key} updated"}
