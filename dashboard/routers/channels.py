import os
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse
import logging
from datetime import datetime

logger = logging.getLogger("evobot.dashboard.channels")

router = APIRouter(prefix="/api/telegram", tags=["channels"])

@router.get("/user")
async def get_telegram_user():
    """Get Telegram user info"""
    from core.telegram_auth import telegram_auth_service
    from config.settings import config
    is_valid, user_info = await telegram_auth_service.check_telegram_session()
    if is_valid and user_info:
        return {
            "user": user_info,
            "api_id": config.telegram.api_id
        }
    return {"user": None, "api_id": None}

@router.get("/user/photo")
async def get_telegram_user_photo():
    """Get Telegram user profile photo"""
    from core.telegram_auth import telegram_auth_service
    is_valid, user_info = await telegram_auth_service.check_telegram_session()
    if is_valid and user_info and user_info.get('photo_path'):
        photo_path = user_info['photo_path']
        if os.path.exists(photo_path):
            return FileResponse(photo_path, media_type="image/jpeg")
    raise HTTPException(status_code=404, detail="Photo not found")

def normalize_channel_id(cid):
    """Standardize channel ID format (usually -100 prefix for public channels)"""
    cid_str = str(cid).strip()
    # If it's a numeric ID that should likely have the -100 prefix but doesn't
    if cid_str.isdigit() and len(cid_str) > 8:
        return f"-100{cid_str}"
    return cid_str

@router.post("/channels/add")
async def add_signal_channels(request: Request):
    """Add signal channels to Firebase configuration"""
    from core.telegram_auth import telegram_auth_service
    from core.firebase_settings import firebase_settings
    from core.firebase_service import firebase_service
    
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authorization")
    
    token = auth_header.split(" ")[1]
    is_valid, payload = telegram_auth_service.verify_token(token)
    if not is_valid or not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    if not firebase_service.db_ref or not firebase_settings._initialized:
        raise HTTPException(status_code=503, detail="Firebase not initialized")
    
    try:
        body = await request.json()
        logger.info(f"Add channels request: {body}")
        
        channels_data = body.get("channels", [])
        channel_ids = body.get("channel_ids", [])
        
        current_channels = list(firebase_settings.signal_channels)
        user_id = payload.get('user_id')
        
        # Process channels with full data
        for channel in channels_data:
            original_id = str(channel.get("id"))
            channel_id = normalize_channel_id(original_id)
            if channel_id not in current_channels:
                current_channels.append(channel_id)
            
            # Store metadata in Firebase
            meta_path = f'users/{user_id}/channels_meta/{channel_id}'
            existing_meta = firebase_service.db_ref.child(meta_path).get() or {}
            
            meta_update = {
                'id': channel_id,
                'title': channel.get('title') or existing_meta.get('title') or f"Channel {channel_id}",
                'username': channel.get('username') or existing_meta.get('username'),
                'verified': channel.get('verified', False) or existing_meta.get('verified', False),
                'has_photo': channel.get('has_photo', False) or existing_meta.get('has_photo', False),
                'participants_count': channel.get('participants_count') or existing_meta.get('participants_count'),
                'updated_at': datetime.utcnow().isoformat()
            }
            firebase_service.db_ref.child(meta_path).set(meta_update)
        
        # Process just IDs
        for channel_id in channel_ids:
            channel_id_str = normalize_channel_id(channel_id)
            if channel_id_str not in current_channels:
                current_channels.append(channel_id_str)
        
        firebase_settings.set("telegram", "signal_channels", current_channels)
        firebase_settings.reload_from_firebase()
        
        logger.info(f"Channels updated. Total: {len(current_channels)}")
        return {"success": True, "channels": current_channels}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding channels: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/channels")
async def get_signal_channels_details(request: Request, refresh: bool = False):
    """Get rich metadata for all signal channels from Firebase"""
    from core.telegram_auth import telegram_auth_service
    from core.firebase_settings import firebase_settings
    from core.firebase_service import firebase_service
    from telegram.listener import telegram_listener
    
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authorization")
    
    token = auth_header.split(" ")[1]
    is_valid, payload = telegram_auth_service.verify_token(token)
    if not is_valid or not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    if not firebase_service.db_ref:
        raise HTTPException(status_code=503, detail="Firebase not initialized")
    
    user_id = payload.get('user_id')
    
    # Get channels from Firebase settings only
    channel_ids = firebase_settings.signal_channels
    logger.info(f"Loading {len(channel_ids)} channels from Firebase: {channel_ids}")
    
    results = []
    if channel_ids:
        meta_ref = firebase_service.db_ref.child(f'users/{user_id}/channels_meta')
        all_meta = meta_ref.get() or {}
        
        # Identify channels that need metadata
        missing_ids = []
        if refresh:
            missing_ids = [cid for cid in channel_ids]
        else:
            for cid in channel_ids:
                cid_str = normalize_channel_id(cid)
                alt_cid = cid_str.replace("-100", "") if cid_str.startswith("-100") else f"-100{cid_str}"
                if cid_str not in all_meta and alt_cid not in all_meta:
                    missing_ids.append(cid)
        
        if missing_ids:
            try:
                if not telegram_listener.client or not telegram_listener.client.is_connected():
                    logger.info("Connecting Telegram listener for metadata fetch...")
                    await telegram_listener.start()
                
                client = telegram_listener.client
                if client and await client.is_user_authorized():
                    from telethon.tl.types import Channel, Chat
                    for cid in missing_ids:
                        try:
                            target = cid
                            if isinstance(cid, str) and cid.startswith("-100"):
                                target = int(cid.replace("-100", ""))
                            elif isinstance(cid, str) and cid.startswith("-"):
                                target = int(cid)
                            elif isinstance(cid, str) and cid.isdigit():
                                target = int(cid)
                            
                            entity = await client.get_entity(target)
                            if isinstance(entity, (Channel, Chat)):
                                photo_path = f"data/channel_photos/{entity.id}.jpg"
                                has_photo = False
                                if entity.photo:
                                    os.makedirs("data/channel_photos", exist_ok=True)
                                    await client.download_profile_photo(entity, file=photo_path)
                                    has_photo = True
                                
                                cid_str = normalize_channel_id(entity.id)
                                meta_update = {
                                    'id': cid_str,
                                    'title': entity.title if hasattr(entity, 'title') else "Unknown",
                                    'username': entity.username if hasattr(entity, 'username') else None,
                                    'verified': getattr(entity, 'verified', False),
                                    'has_photo': has_photo,
                                    'participants_count': getattr(entity, 'participants_count', None),
                                    'updated_at': datetime.utcnow().isoformat()
                                }
                                meta_ref.child(cid_str).set(meta_update)
                                all_meta[cid_str] = meta_update
                        except Exception as ce:
                            logger.warning(f"Could not fetch metadata for {cid}: {ce}")
            except Exception as e:
                logger.error(f"Error auto-fetching channels: {e}")

        # Collect results
        for cid in channel_ids:
            cid_str = normalize_channel_id(cid)
            info = all_meta.get(cid_str) or all_meta.get(cid_str.replace("-100", "")) or all_meta.get(f"-100{cid_str}")
            
            if info:
                results.append(info)
            else:
                results.append({
                    "id": cid_str,
                    "title": f"Channel {cid_str.replace('-100', '')}",
                    "username": None,
                    "has_photo": False
                })
    
    return {"channels": results}

@router.get("/search-channels")
async def search_telegram_channels(query: str = "", request: Request = None):
    """Search for Telegram channels/groups"""
    from core.telegram_auth import telegram_auth_service
    from telegram.listener import telegram_listener
    from telethon.tl.types import Channel, Chat
    
    # Verify authentication
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authorization")
    
    token = auth_header.split(" ")[1]
    is_valid, payload = telegram_auth_service.verify_token(token)
    if not is_valid or not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    results = []
    try:
        if not telegram_listener.client or not telegram_listener.client.is_connected():
            logger.info("Connecting Telegram listener for channel search...")
            await telegram_listener.start()
            
        client = telegram_listener.client
        if not client or not await client.is_user_authorized():
            raise HTTPException(status_code=401, detail="Telegram session not authorized")
        
        logger.info(f"Fetching dialogs with query: '{query}'")
        dialogs = await client.get_dialogs(limit=100)
        logger.info(f"Found {len(dialogs)} total dialogs")
        
        for dialog in dialogs:
            entity = dialog.entity
            if isinstance(entity, (Channel, Chat)):
                if query and query.lower() not in (entity.title or "").lower():
                    continue
                
                photo_path = None
                if entity.photo:
                    try:
                        photo_dir = "data/channel_photos"
                        os.makedirs(photo_dir, exist_ok=True)
                        photo_path = f"{photo_dir}/{entity.id}.jpg"
                        if not os.path.exists(photo_path):
                            await client.download_profile_photo(entity, file=photo_path)
                    except: pass
                
                eid_str = normalize_channel_id(entity.id)
                results.append({
                    "id": eid_str,
                    "title": entity.title if hasattr(entity, 'title') else "Unknown",
                    "username": entity.username if hasattr(entity, 'username') else None,
                    "participants_count": getattr(entity, 'participants_count', None),
                    "verified": getattr(entity, 'verified', False),
                    "has_photo": photo_path is not None and os.path.exists(photo_path)
                })
        
        logger.info(f"Returning {len(results)} channels after filtering")
        results.sort(key=lambda x: (not x.get('verified', False), -(x.get('participants_count') or 0)))
        return {"channels": results[:50]}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching Telegram channels: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/channel/{channel_id}/photo")
async def get_channel_photo(channel_id: str):
    """Get channel profile photo"""
    # Try both original ID and ID without -100 prefix (Telethon saves by raw ID)
    clean_id = channel_id.replace("-100", "")
    paths = [
        f"data/channel_photos/{channel_id}.jpg",
        f"data/channel_photos/{clean_id}.jpg"
    ]
    for path in paths:
        if os.path.exists(path):
            return FileResponse(path, media_type="image/jpeg")
    raise HTTPException(status_code=404, detail="Photo not found")

@router.post("/channels/remove")
async def remove_signal_channel(request: Request):
    """Remove a signal channel from Firebase configuration"""
    from core.telegram_auth import telegram_auth_service
    from core.firebase_settings import firebase_settings
    from core.firebase_service import firebase_service
    
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authorization")
    
    token = auth_header.split(" ")[1]
    is_valid, payload = telegram_auth_service.verify_token(token)
    if not is_valid or not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    if not firebase_service.db_ref or not firebase_settings._initialized:
        raise HTTPException(status_code=503, detail="Firebase not initialized")
    
    try:
        body = await request.json()
        channel_id = body.get("channel_id")
        if not channel_id:
            raise HTTPException(status_code=400, detail="No channel ID provided")
        
        current_channels = list(firebase_settings.signal_channels)
        user_id = payload.get('user_id')
        
        norm_id = normalize_channel_id(channel_id)
        alt_id = norm_id.replace("-100", "") if norm_id.startswith("-100") else f"-100{norm_id}"
        
        logger.info(f"Removing channel: {channel_id} (normalized: {norm_id})")
        
        new_channels = []
        found = False
        for c in current_channels:
            c_norm = normalize_channel_id(c)
            if c_norm == norm_id or c_norm == alt_id:
                found = True
                logger.info(f"Matched and removing: {c}")
                continue
            new_channels.append(c)
            
        if found:
            firebase_settings.set("telegram", "signal_channels", new_channels)
            firebase_settings.reload_from_firebase()
            
            # Cleanup metadata
            firebase_service.db_ref.child(f'users/{user_id}/channels_meta/{norm_id}').delete()
            clean_id = norm_id.replace("-100", "").replace("-", "")
            firebase_service.db_ref.child(f'users/{user_id}/channels_meta/{clean_id}').delete()
            
            logger.info(f"Channel removed. New count: {len(new_channels)}")
        else:
            logger.warning(f"Channel {channel_id} not found")
        
        return {"success": True, "channels": new_channels}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing channel: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
