from .base import *
from dotenv import load_dotenv

load_dotenv()

DEBUG = True
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
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

CLOUDINARY_STORAGE = {
    'CLOUD_NAME': os.getenv('CLOUDINARY_CLOUD_NAME'),
    'API_KEY': os.getenv('CLOUDINARY_API_KEY'),
    'API_SECRET': os.getenv('CLOUDINARY_API_SECRET')
}

STORAGES = {
    "default": {
        "BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage",
    },
    "staticfiles": {
        "BACKEND": "cloudinary_storage.storage.StaticHashedCloudinaryStorage",
    },
}

STATICFILES_STORAGE = STORAGES["staticfiles"]["BACKEND"]