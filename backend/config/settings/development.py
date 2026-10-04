from .base import *


DEBUG = True

ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
]

CORS_ALLOWED_ORIGINS = env.list(
    "CORS_ALLOWED_ORIGINS",
    default=[
        "http://localhost:5173",
    ],
)
CORS_ALLOW_CREDENTIALS = True