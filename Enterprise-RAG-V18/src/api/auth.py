# src/api/auth.py
import jwt
import logging
from fastapi import Request, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from configs.settings import settings

logger = logging.getLogger(__name__)

security = HTTPBearer()

async def verify_jwt(credentials: HTTPAuthorizationCredentials = Security(security)) -> dict:
    """Layer 4a: JWT RS256 validation"""
    if not settings.JWT_PUBLIC_KEY:
        if settings.ALLOW_DEV_AUTH:
            return {"sub": "dev_user", "roles": ["admin"]}
        raise HTTPException(status_code=401, detail="JWT_PUBLIC_KEY not configured")
        
    try:
        token = credentials.credentials
        
        # We assume the public key is provided in PEM format in settings
        public_key = settings.JWT_PUBLIC_KEY.replace("\\n", "\n")
        
        claims = jwt.decode(
            token,
            public_key,
            algorithms=[settings.JWT_ALGORITHM],
            options={"verify_exp": True, "verify_iat": True}
        )
        
        if not claims.get("sub"):
            raise HTTPException(status_code=401, detail="Missing 'sub' claim")
            
        return claims
    except jwt.ExpiredSignatureError:
        logger.warning("Token expired")
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        logger.error(f"Auth error: {e}")
        raise HTTPException(status_code=401, detail="Authentication failed")
