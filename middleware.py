from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from jose import jwt, JWTError
from auth import SECRET_KEY, ALGORITHM
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import logging

logger = logging.getLogger("uvicorn")

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        logger.debug(f"AuthMiddleware triggered for path: {request.url.path}")
        
        public_routes = ["/", "/login/", "/register/","/docs", "/redoc", "/openapi.json"]
        if request.url.path in public_routes or any(request.url.path.startswith(route) for route in public_routes[1:]):
            logger.debug(f"Middleware bypassed for path: {request.url.path}")
            return await call_next(request)
        
        auth_header = request.headers.get("Authorization")
        # logger.debug(f"Authentication header-----> {auth_header}")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Authorization header missing or invalid"}
            )
        
        token = auth_header.split(" ")[1]
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            # logger.info(f"Decoded JWT payload: {payload}")
            request.state.user = payload
        except JWTError as e:
            logger.error(f"JWT decoding failed: {e}")
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid or expired token"}
            )

        return await call_next(request)

