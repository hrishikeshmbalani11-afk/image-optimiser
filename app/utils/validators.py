from pathlib import Path

from PIL import Image, UnidentifiedImageError


def validate_upload(uploaded_file, config):
    filename = uploaded_file.filename or ""
    if not filename:
        return False, "Please choose an image file.", None

    extension = Path(filename).suffix.lower()
    if extension not in config["ALLOWED_EXTENSIONS"]:
        return False, "Only JPEG, PNG, and WebP are supported.", None

    if uploaded_file.mimetype not in config["ALLOWED_MIME_TYPES"]:
        return False, "Only JPEG, PNG, and WebP MIME types are allowed.", None

    try:
        image = Image.open(uploaded_file.stream)
        pil_format = (image.format or "").upper()
        image.verify()
    except (UnidentifiedImageError, OSError):
        uploaded_file.stream.seek(0)
        return False, "Invalid image file.", None
    finally:
        uploaded_file.stream.seek(0)

    if pil_format not in config["ALLOWED_PIL_FORMATS"]:
        return False, "Only JPEG, PNG, and WebP image formats are supported.", None

    return True, "", pil_format
