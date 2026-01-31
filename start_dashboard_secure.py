#!/usr/bin/env python3
"""
Dashboard Startup Script with Authentication Verification
Ensures all authentication components are properly configured before starting
"""

import os
import sys
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("startup")

def check_dependencies():
    """Check if required packages are installed"""
    logger.info("Checking dependencies...")
    
    required = {
        'fastapi': 'FastAPI',
        'uvicorn': 'Uvicorn',
        'firebase_admin': 'Firebase Admin SDK',
        'jwt': 'PyJWT',
        'bcrypt': 'bcrypt'
    }
    
    missing = []
    for module, name in required.items():
        try:
            __import__(module)
            logger.info(f"  ✓ {name}")
        except ImportError:
            logger.error(f"  ✗ {name} not installed")
            missing.append(name)
    
    if missing:
        logger.error(f"\nMissing dependencies: {', '.join(missing)}")
        logger.error("Install with: pip install -r requirements.txt -r requirements_firebase.txt")
        return False
    
    return True

def check_environment():
    """Check environment variables"""
    logger.info("\nChecking environment configuration...")
    
    # Optional Firebase variables
    firebase_vars = [
        'FIREBASE_PROJECT_ID',
        'FIREBASE_PRIVATE_KEY',
        'FIREBASE_CLIENT_EMAIL'
    ]
    
    firebase_configured = all(os.getenv(var) for var in firebase_vars)
    
    if firebase_configured:
        logger.info("  ✓ Firebase credentials configured")
    else:
        logger.warning("  ⚠ Firebase credentials not configured (will use local auth)")
    
    # JWT Secret
    jwt_secret = os.getenv('JWT_SECRET_KEY')
    if jwt_secret and jwt_secret != 'your-secret-key-change-in-production':
        logger.info("  ✓ JWT secret key configured")
    else:
        logger.warning("  ⚠ Using default JWT secret (change in production!)")
    
    return True

def ensure_directories():
    """Ensure required directories exist"""
    logger.info("\nEnsuring directories exist...")
    
    dirs = ['data', 'logs']
    for dir_name in dirs:
        os.makedirs(dir_name, exist_ok=True)
        logger.info(f"  ✓ {dir_name}/")
    
    return True

def initialize_auth():
    """Initialize authentication system"""
    logger.info("\nInitializing authentication system...")
    
    try:
        from core.firebase_auth import init_firebase_auth
        
        auth_service = init_firebase_auth()
        logger.info("  ✓ Authentication service initialized")
        
        # Verify default admin exists
        admin = auth_service.get_user("admin@evobot.local")
        if admin:
            logger.info("  ✓ Default admin user exists")
        else:
            logger.warning("  ⚠ Default admin user not found")
        
        return True
    except Exception as e:
        logger.error(f"  ✗ Failed to initialize auth: {e}")
        return False

def start_dashboard():
    """Start the dashboard server"""
    logger.info("\n" + "="*60)
    logger.info("Starting EvoBot Dashboard...")
    logger.info("="*60)
    
    try:
        import uvicorn
        from dashboard.app import app
        
        host = os.getenv("DASHBOARD_HOST", "0.0.0.0")
        port = int(os.getenv("DASHBOARD_PORT", "8080"))
        
        logger.info(f"\n🚀 Dashboard will be available at:")
        logger.info(f"   http://localhost:{port}")
        logger.info(f"   http://127.0.0.1:{port}")
        logger.info(f"\n📝 Default admin credentials:")
        logger.info(f"   Email: admin@evobot.local")
        logger.info(f"   Password: Admin@123!")
        logger.info(f"\n⚠️  Change the default password after first login!\n")
        
        uvicorn.run(
            app,
            host=host,
            port=port,
            log_level="warning",
            access_log=False
        )
    except KeyboardInterrupt:
        logger.info("\n\nShutting down gracefully...")
    except Exception as e:
        logger.error(f"\n✗ Failed to start dashboard: {e}")
        sys.exit(1)

def main():
    """Main startup sequence"""
    print("\n" + "="*60)
    print("EvoBot Dashboard - Startup Verification")
    print("="*60 + "\n")
    
    # Run checks
    checks = [
        ("Dependencies", check_dependencies),
        ("Environment", check_environment),
        ("Directories", ensure_directories),
        ("Authentication", initialize_auth)
    ]
    
    for check_name, check_func in checks:
        if not check_func():
            logger.error(f"\n✗ {check_name} check failed!")
            logger.error("Please fix the issues above and try again.")
            sys.exit(1)
    
    logger.info("\n✓ All checks passed!")
    
    # Start dashboard
    start_dashboard()

if __name__ == "__main__":
    main()
