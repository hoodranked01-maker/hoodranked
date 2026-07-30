from .base import *
from dotenv import load_dotenv

load_dotenv()

DEBUG = False
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY')

ALLOWED_HOSTS = ['hoodranked.store', 'www.hoodranked.store', '*.ngrok-free.dev']

# Production Database (PostgreSQL)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('PROD_DB_NAME'),
        'USER': os.getenv('PROD_DB_USER'),
        'PASSWORD': os.getenv('PROD_DB_PASSWORD'),
        'HOST': os.getenv('PROD_DB_HOST'),
        'PORT': os.getenv('PROD_DB_PORT'),
    }
}

# Security settings
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Email (configure later with SendGrid or similar)
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# Static and media (production/cloud)
# Serve static from Supabase/S3 endpoint when configured
STATIC_URL = f"{AWS_S3_ENDPOINT_URL}/{AWS_STORAGE_BUCKET_NAME}/static/" if AWS_S3_ENDPOINT_URL else '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = f"{AWS_S3_ENDPOINT_URL}/{AWS_STORAGE_BUCKET_NAME}/media/" if AWS_S3_ENDPOINT_URL else '/media/'

# Use custom storage backend for static files (public) and S3-like storage for default files
STATICFILES_STORAGE = 'main.settings.custom_storages.SupabasePublicStaticStorage'
DEFAULT_FILE_STORAGE = 'storages.backends.s3.S3Storage'

# Storages configuration (Supabase/S3)
STORAGES = {
    "default": {
        "BACKEND": "storages.backends.s3.S3Storage",
        "OPTIONS": {
            "access_key": AWS_ACCESS_KEY_ID,
            "secret_key": AWS_SECRET_ACCESS_KEY,
            "bucket_name": AWS_STORAGE_BUCKET_NAME,
            "endpoint_url": AWS_S3_ENDPOINT_URL,
            "region_name": AWS_S3_REGION_NAME,
            "signature_version": AWS_S3_SIGNATURE_VERSION,
            "querystring_auth": AWS_QUERYSTRING_AUTH,
        },
    },
    "staticfiles": {
        "BACKEND": "main.settings.custom_storages.SupabasePublicStaticStorage",
        "OPTIONS": {
            "access_key": AWS_ACCESS_KEY_ID,
            "secret_key": AWS_SECRET_ACCESS_KEY,
            "bucket_name": AWS_STORAGE_BUCKET_NAME,
            "endpoint_url": AWS_S3_ENDPOINT_URL,
            "region_name": AWS_S3_REGION_NAME,
            "signature_version": AWS_S3_SIGNATURE_VERSION,
            "location": "static",
            "querystring_auth": False,
        },
    },
}