import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# This dependency scheme will extract the bearer token from the "Authorization" header.
http_bearer = HTTPBearer(auto_error=False)

async def verify_sso_token(token: str):
    """
    Verifies the SSO token with your authentication gateway using an async request.
    This function replaces the synchronous `requests` version.
    """
    sso_service_url = "https://jktech-auth-gateway-140475459295.asia-south1.run.app/verify"
    headers = {"Authorization": f"Bearer {token}"}

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(sso_service_url, headers=headers)

            # Check for a successful response from the SSO service.
            if response.status_code == 200:
                sso_response = response.json()
                # return sso_response
                # Explicitly check for a "valid": true key in the response.
                if sso_response.get("valid") is True:
                    return sso_response
            
            # If the status is not 200 or the "valid" key is not true, deny access.
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired SSO token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        except httpx.RequestError:
            # This catches network issues like connection errors or timeouts.
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Could not connect to the SSO authentication service.",
            )

async def sso_security(creds: HTTPAuthorizationCredentials = Depends(http_bearer)):
    """
    A FastAPI dependency that retrieves a bearer token from the request and 
    verifies it using the external SSO service.
    """
    if creds is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer token not provided",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = creds.credentials
    sso_payload = await verify_sso_token(token)
    
    # The payload from the SSO service can be returned and used in your routes if needed.
    return sso_payload
