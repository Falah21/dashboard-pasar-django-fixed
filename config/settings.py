import os
from pathlib import Path
import dj_database_url
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


# =========================================================
# HELPER: Baca env CSV
# =========================================================
def csv_env(name, default=""):
    """Baca env variable yang berisi daftar dipisah koma."""
    raw = os.getenv(name, default)
    return [item.strip() for item in raw.split(",") if item.strip()]


def bool_env(name, default=False):
    """Baca env variable boolean."""
    val = os.getenv(name, str(default)).strip().lower()
    return val in {"1", "true", "yes", "on"}


# =========================================================
# CORE SECURITY
# =========================================================
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError(
        "SECRET_KEY belum di-set. "
        "Buat di .env atau di Railway Variables."
    )

DEBUG = bool_env("DEBUG", False)   # ⭐ default False di production

ALLOWED_HOSTS = csv_env(
    "ALLOWED_HOSTS",
    "127.0.0.1,localhost"
)

# Railway auto-generate domain seperti *.up.railway.app
# Kita tambahkan otomatis via env RAILWAY_PUBLIC_DOMAIN
railway_domain = os.getenv("RAILWAY_PUBLIC_DOMAIN")
if railway_domain and railway_domain not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(railway_domain)

CSRF_TRUSTED_ORIGINS = csv_env(
    "CSRF_TRUSTED_ORIGINS",
    ""
)
# Auto-add Railway domain kalau ada
if railway_domain:
    https_origin = f"https://{railway_domain}"
    if https_origin not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(https_origin)


# =========================================================
# APPS
# =========================================================
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "dashboard",
]


# =========================================================
# MIDDLEWARE
# =========================================================
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",           # static files
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


# =========================================================
# URLS & TEMPLATES
# =========================================================
ROOT_URLCONF = "config.urls"

TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [BASE_DIR / "templates"],
    "APP_DIRS": True,
    "OPTIONS": {
        "context_processors": [
            "django.template.context_processors.debug",
            "django.template.context_processors.request",
            "django.contrib.auth.context_processors.auth",
            "django.contrib.messages.context_processors.messages",
        ],
    },
}]

WSGI_APPLICATION = "config.wsgi.application"


# =========================================================
# DATABASE — Supabase PostgreSQL
# =========================================================
database_url = os.getenv("DATABASE_URL", "").strip()

if database_url:
    DATABASES = {
        "default": dj_database_url.parse(
            database_url,
            conn_max_age=600,
            conn_health_checks=True,
            ssl_require=True,          # ⭐ Supabase wajib SSL
        )
    }
    # Supabase pooler kadang butuh "OPTIONS" ini
    DATABASES["default"].setdefault("OPTIONS", {})
    DATABASES["default"]["OPTIONS"]["sslmode"] = "require"
else:
    # Fallback ke SQLite (development lokal)
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }


# =========================================================
# AUTH
# =========================================================
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Login URLs (kalau nanti butuh)
LOGIN_URL = "/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/login/"


# =========================================================
# INTERNATIONALIZATION
# =========================================================
LANGUAGE_CODE = "id"
TIME_ZONE = "Asia/Jakarta"
USE_I18N = True
USE_TZ = True


# =========================================================
# STATIC & MEDIA FILES
# =========================================================
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage"
    },
    "staticfiles": {
        "BACKEND": (
            "django.contrib.staticfiles.storage.StaticFilesStorage"
            if DEBUG
            else "whitenoise.storage.CompressedManifestStaticFilesStorage"
        )
    },
}

# ⚠️ Railway filesystem ephemeral — media files akan hilang saat restart.
# Kalau butuh simpan media permanen, pakai Supabase Storage / S3.
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"


# =========================================================
# DEFAULT PRIMARY KEY
# =========================================================
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# =========================================================
# UPLOAD LIMITS
# =========================================================
# ⚠️ Railway punya batas request size (biasanya 100 MB di proxy)
DATA_UPLOAD_MAX_MEMORY_SIZE = 100 * 1024 * 1024         # 100 MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 100 * 1024 * 1024         # 100 MB
DATA_UPLOAD_MAX_NUMBER_FILES = 200
DATA_UPLOAD_MAX_NUMBER_FIELDS = 10000                   # untuk filter banyak

MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "100"))


# =========================================================
# SECURITY HEADERS (Production)
# =========================================================
# Aktifkan kalau sudah HTTPS (Railway auto HTTPS)
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")   # Railway pakai reverse proxy
    SECURE_SSL_REDIRECT = True                                       # redirect HTTP → HTTPS
    SESSION_COOKIE_SECURE = True                                     # cookie hanya via HTTPS
    CSRF_COOKIE_SECURE = True                                        # CSRF cookie hanya via HTTPS
    SECURE_HSTS_SECONDS = 31536000                                   # 1 tahun
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = "DENY"
SECURE_REFERRER_POLICY = "same-origin"


# =========================================================
# LOGGING — Production
# =========================================================
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": os.getenv("DJANGO_LOG_LEVEL", "INFO"),
            "propagate": False,
        },
        "django.db.backends": {
            "handlers": ["console"],
            "level": "WARNING",     # set INFO kalau mau lihat query SQL
            "propagate": False,
        },
    },
}


# =========================================================
# CACHES (opsional — pakai Redis kalau Railway add-on)
# =========================================================
# Uncomment kalau mau pakai Redis
# REDIS_URL = os.getenv("REDIS_URL", "")
# if REDIS_URL:
#     CACHES = {
#         "default": {
#             "BACKEND": "django.core.cache.backends.redis.RedisCache",
#             "LOCATION": REDIS_URL,
#         }
#     }
