from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
TEMP_DIR = BASE_DIR / "temp"


class Config:
    SECRET_KEY = "dev-change-me"
    MAX_CONTENT_LENGTH = 25 * 1024 * 1024  # 25MB

    ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
    ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}
    ALLOWED_PIL_FORMATS = {"JPEG", "PNG", "WEBP"}

    DEFAULT_PRESET = "balanced"
    DEFAULT_QUALITY = 85
    DEFAULT_RESIZE_PERCENT = 100
    DEFAULT_STRIP_METADATA = True
    DEFAULT_AUTO_ORIENT = True
    DEFAULT_SHARPNESS_BALANCE = 0.0
    DEFAULT_CONTRAST = 1.0
    DEFAULT_BRIGHTNESS = 1.0

    SHARPNESS_BALANCE_RANGE = (-5.0, 5.0)
    CONTRAST_RANGE = (0.5, 2.0)
    BRIGHTNESS_RANGE = (0.5, 2.0)

    QUALITY_PRESET_BOUNDS = {
        "speed": (30, 50),
        "balanced": (50, 75),
        "max_quality": (80, 95),
        "custom_quality": (1, 95),
    }

    UPLOAD_FOLDER = TEMP_DIR / "uploads"
    PROCESSED_FOLDER = TEMP_DIR / "processed"
    TEMP_FILE_MAX_AGE_SECONDS = 60 * 60  # 1 hour
    CLEANUP_INTERVAL_SECONDS = 60

    RATELIMIT_STORAGE_URI = "memory://"
