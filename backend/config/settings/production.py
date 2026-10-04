from .base import *


DEBUG = False

ALLOWED_HOSTS = []

ENABLE_API_DOCS = env.bool("ENABLE_API_DOCS", default=False)

CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=[])
CORS_ALLOW_CREDENTIALS = True