from fastapi import FastAPI
from starlette.middleware import Middleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

class LimitUploadSizeMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_upload_size: int):
        super().__init__(app)
        self.max_upload_size = max_upload_size  # in bytes

    async def dispatch(self, request: Request, call_next):
        if request.headers.get('content-length') is not None:
            content_length = int(request.headers['content-length'])
            if content_length > self.max_upload_size:
                return Response(
                    content="Request too large",
                    status_code=413
                )
        return await call_next(request)
