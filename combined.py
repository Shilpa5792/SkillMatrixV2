# app/security/combined.py
from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_db
from app.crud.admin import get_admin_by_id
from app.security.deps import decode_admin_token
from app.security.sso import verify_sso_token
import logging


logger = logging.getLogger("auth")
http_bearer = HTTPBearer(auto_error=False)

async def authorize_user(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    # Extract bearer token once
    creds = await http_bearer(request)
    logger.info("AUTH.START received_request")
    if creds is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer token not provided",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = creds.credentials
    logger.info("AUTH.TOKEN_EXTRACTED token_present")

    try:
        logger.info("AUTH.ADMIN.JWT_DECODE start_decode")
        sub = decode_admin_token(token)
        logger.info("AUTH.ADMIN.JWT_DECODE success sub=%s", sub)
        logger.info("AUTH.ADMIN.DB_LOOKUP start_lookup sub=%s", sub)
        admin = await get_admin_by_id(db, sub)

        if admin:
            logger.info("AUTH.ADMIN.DB_LOOKUP found sub=%s", sub)   
            logger.info("AUTH.SUCCESS admin_authenticated sub=%s", sub)
            return admin
        logger.info("AUTH.SSO.VERIFY start_verify")
        sso_user = await verify_sso_token(token)
        logger.info("AUTH.SSO.VERIFY success user=%s", sso_user)
        return sso_user
            
    except HTTPException as e:
        logger.warning("AUTH.ADMIN.JWT_DECODE failed error=%s", str(e))
        auth_exception = e  # Save for later

