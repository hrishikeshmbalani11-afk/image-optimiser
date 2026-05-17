import base64
from io import BytesIO
from pathlib import Path

from flask import Blueprint, current_app, jsonify, render_template, request
from PIL import Image, ImageEnhance, ImageFilter, ImageOps

from .extensions import limiter
from .utils.validators import validate_upload

main_bp = Blueprint("main", __name__)


@main_bp.get("/")
def index():
    return render_template("index.html")


@main_bp.post("/optimize")
@limiter.limit("30 per minute")
def optimize_image():
    if "image" not in request.files:
        return jsonify({"ok": False, "error": "No file provided."}), 400

    uploaded_file = request.files["image"]
    is_valid, error, detected_format = validate_upload(uploaded_file, current_app.config)
    if not is_valid:
        return jsonify({"ok": False, "error": error}), 400

    config = current_app.config
    preset = request.form.get("preset", config["DEFAULT_PRESET"]).strip().lower()
    if preset not in config["QUALITY_PRESET_BOUNDS"]:
        return jsonify({"ok": False, "error": "Invalid preset."}), 400

    quality = _parse_int(
        request.form.get("quality"),
        default=config["DEFAULT_QUALITY"],
        min_value=1,
        max_value=95,
    )
    resize_percent = _parse_int(
        request.form.get("resize_percent"),
        default=config["DEFAULT_RESIZE_PERCENT"],
        min_value=10,
        max_value=200,
    )
    strip_metadata = _parse_bool(
        request.form.get("strip_metadata"),
        default=config["DEFAULT_STRIP_METADATA"],
    )
    auto_orient = _parse_bool(
        request.form.get("auto_orient"),
        default=config["DEFAULT_AUTO_ORIENT"],
    )
    sharpness_balance = _parse_float(
        request.form.get("sharpness_balance"),
        default=config["DEFAULT_SHARPNESS_BALANCE"],
        min_value=config["SHARPNESS_BALANCE_RANGE"][0],
        max_value=config["SHARPNESS_BALANCE_RANGE"][1],
    )
    contrast = _parse_float(
        request.form.get("contrast"),
        default=config["DEFAULT_CONTRAST"],
        min_value=config["CONTRAST_RANGE"][0],
        max_value=config["CONTRAST_RANGE"][1],
    )
    brightness = _parse_float(
        request.form.get("brightness"),
        default=config["DEFAULT_BRIGHTNESS"],
        min_value=config["BRIGHTNESS_RANGE"][0],
        max_value=config["BRIGHTNESS_RANGE"][1],
    )
    output_format = request.form.get("output_format", detected_format).strip().upper()
    if output_format not in config["ALLOWED_PIL_FORMATS"]:
        return jsonify({"ok": False, "error": "Invalid output format."}), 400

    effective_quality, quality_note = _effective_quality(quality, preset, config)

    uploaded_file.stream.seek(0)
    original_bytes = uploaded_file.stream.read()
    before_size = len(original_bytes)
    uploaded_file.stream.seek(0)

    image = Image.open(BytesIO(original_bytes))
    source_info = dict(image.info)
    if auto_orient:
        image = ImageOps.exif_transpose(image)

    before_width, before_height = image.size
    if resize_percent != 100:
        new_width = max(1, round(image.width * resize_percent / 100))
        new_height = max(1, round(image.height * resize_percent / 100))
        image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

    image = _apply_enhancements(
        image=image,
        sharpness_balance=sharpness_balance,
        contrast=contrast,
        brightness=brightness,
    )
    after_width, after_height = image.size

    output_buffer = BytesIO()
    save_kwargs = _save_kwargs(
        output_format=output_format,
        preset=preset,
        quality=effective_quality,
        strip_metadata=strip_metadata,
        source_info=source_info,
    )
    image = _normalize_mode_for_format(image, output_format)
    image.save(output_buffer, format=output_format, **save_kwargs)

    after_bytes = output_buffer.getvalue()
    after_size = len(after_bytes)

    reduction_percent = 0.0
    size_change_percent = 0.0
    if before_size > 0:
        reduction_percent = ((before_size - after_size) / before_size) * 100
        size_change_percent = ((after_size - before_size) / before_size) * 100

    mime_type = _mime_for_format(output_format)
    after_data_url = f"data:{mime_type};base64,{base64.b64encode(after_bytes).decode('ascii')}"
    original_name = Path(uploaded_file.filename or "image").stem
    extension = _ext_for_format(output_format)

    return jsonify(
        {
            "ok": True,
            "after_data_url": after_data_url,
            "after_filename": f"{original_name}-optimized{extension}",
            "before_size": before_size,
            "after_size": after_size,
            "before_width": before_width,
            "before_height": before_height,
            "after_width": after_width,
            "after_height": after_height,
            "reduction_percent": round(reduction_percent, 2),
            "size_change_percent": round(size_change_percent, 2),
            "effective_quality": effective_quality,
            "preset": preset,
            "quality_note": quality_note,
            "resize_percent": resize_percent,
            "output_format": output_format,
            "input_format": detected_format,
            "sharpness_balance": sharpness_balance,
            "contrast": contrast,
            "brightness": brightness,
            "strip_metadata": strip_metadata,
            "auto_orient": auto_orient,
        }
    )


def _parse_int(raw_value, default: int, min_value: int, max_value: int) -> int:
    try:
        value = int(raw_value)
    except (TypeError, ValueError):
        value = default
    return min(max(value, min_value), max_value)


def _parse_bool(raw_value, default: bool) -> bool:
    if raw_value is None:
        return default
    return str(raw_value).strip().lower() in {"1", "true", "yes", "on"}


def _parse_float(raw_value, default: float, min_value: float, max_value: float) -> float:
    try:
        value = float(raw_value)
    except (TypeError, ValueError):
        value = default
    return min(max(value, min_value), max_value)


def _effective_quality(requested_quality: int, preset: str, config) -> tuple[int, str]:
    if preset == "custom_quality":
        return min(max(requested_quality, 1), 95), ""

    min_quality, max_quality = config["QUALITY_PRESET_BOUNDS"][preset]
    effective_quality = min(max(requested_quality, min_quality), max_quality)
    if effective_quality == requested_quality:
        return effective_quality, ""
    return (
        effective_quality,
        f"Preset '{preset}' softly clamps quality to {min_quality}-{max_quality}.",
    )


def _normalize_mode_for_format(image: Image.Image, detected_format: str) -> Image.Image:
    if detected_format == "JPEG" and image.mode not in ("RGB", "L"):
        return image.convert("RGB")
    return image


def _apply_enhancements(
    image: Image.Image,
    sharpness_balance: float,
    contrast: float,
    brightness: float,
) -> Image.Image:
    if sharpness_balance < 0:
        image = image.filter(ImageFilter.GaussianBlur(radius=abs(sharpness_balance)))
    elif sharpness_balance > 0:
        sharpen_factor = 1.0 + ((sharpness_balance / 5.0) * 2.0)  # 1.0 -> 3.0
        image = ImageEnhance.Sharpness(image).enhance(sharpen_factor)
    if contrast != 1.0:
        image = ImageEnhance.Contrast(image).enhance(contrast)
    if brightness != 1.0:
        image = ImageEnhance.Brightness(image).enhance(brightness)
    return image


def _save_kwargs(output_format: str, preset: str, quality: int, strip_metadata: bool, source_info: dict) -> dict:
    preset_map = {
        "speed": {"jpeg_subsampling": 2, "webp_method": 1, "png_compress": 3},
        "balanced": {"jpeg_subsampling": 1, "webp_method": 4, "png_compress": 6},
        "max_quality": {"jpeg_subsampling": 0, "webp_method": 6, "png_compress": 9},
        "custom_quality": {"jpeg_subsampling": 1, "webp_method": 4, "png_compress": 6},
    }
    mapped = preset_map[preset]
    save_kwargs: dict = {}

    if output_format == "JPEG":
        save_kwargs.update(
            {
                "quality": quality,
                "subsampling": mapped["jpeg_subsampling"],
                "optimize": preset != "speed",
                "progressive": preset != "speed",
            }
        )
    elif output_format == "WEBP":
        save_kwargs.update({"quality": quality, "method": mapped["webp_method"]})
    elif output_format == "PNG":
        save_kwargs.update({"optimize": True, "compress_level": mapped["png_compress"]})

    if not strip_metadata:
        exif = source_info.get("exif")
        icc_profile = source_info.get("icc_profile")
        if exif:
            save_kwargs["exif"] = exif
        if icc_profile:
            save_kwargs["icc_profile"] = icc_profile

    return save_kwargs


def _mime_for_format(detected_format: str) -> str:
    return {
        "JPEG": "image/jpeg",
        "PNG": "image/png",
        "WEBP": "image/webp",
    }[detected_format]


def _ext_for_format(detected_format: str) -> str:
    return {
        "JPEG": ".jpg",
        "PNG": ".png",
        "WEBP": ".webp",
    }[detected_format]
