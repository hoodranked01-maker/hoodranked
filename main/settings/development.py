from .base import *

DEBUG = True
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'django-insecure-dev-key-change-in-production')

ALLOWED_HOSTS = ['*']

# Use SQLite for local development (easier)
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#     }
# }

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

# Email - Console backend for development
# EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Static and media (development/local)
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

# Use WhiteNoise in development to serve static files locally

# Storages configuration (Supabase/S3)
# STORAGES = {
#     "default": {
#         "BACKEND": "storages.backends.s3.S3Storage",
#         "OPTIONS": {
#             "access_key": AWS_ACCESS_KEY_ID,
#             "secret_key": AWS_SECRET_ACCESS_KEY,
#             "bucket_name": AWS_STORAGE_BUCKET_NAME,
#             "endpoint_url": AWS_S3_ENDPOINT_URL,
#             "region_name": AWS_S3_REGION_NAME,
#             "signature_version": AWS_S3_SIGNATURE_VERSION,
#             "querystring_auth": AWS_QUERYSTRING_AUTH,
#         },
#     },
#     "staticfiles": {
#         "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
#     },
# }

STORAGES = {
    "default": {
        "BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage",
    },
    "staticfiles": {
        "BACKEND": "cloudinary_storage.storage.StaticHashedCloudinaryStorage",
    },
}