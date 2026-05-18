# Session Notes

## SESSION 1:

## 1. Project Overview
This project is a Flask-based web application for interactive image optimization.  
It provides a drag-and-drop user experience where users can upload an image, configure optimization settings, and immediately compare **Before** and **After** images side-by-side.

The app currently focuses on robust upload/validation behavior, practical optimization controls, and clear visual feedback, while keeping the codebase ready for future additions (including OpenCV-backed features).

---

## 2. Core Product Goals
1. Accept only safe/expected image formats.
2. Provide meaningful optimization controls without a complicated UI.
3. Display real optimization output and metadata for user trust.
4. Keep request handling and temporary data lifecycle manageable.
5. Maintain a clean, extensible Flask project structure.

---

## 3. Current Feature Set

### Upload & Validation
- Supported formats: **JPEG, PNG, WebP**
- Rejected formats include SVG/GIF by policy.
- Validation checks include:
  - Extension allow-list
  - MIME type allow-list
  - Pillow format detection/verification
- Max upload size: **25MB** (`MAX_CONTENT_LENGTH`)

### Security & Request Control
- Global and endpoint-level rate limiting through Flask-Limiter:
  - **30 requests/min per IP**

### Optimization Controls
- Presets:
  - `speed`
  - `balanced` (default)
  - `max_quality`
  - `custom_quality` (enables slider)
- Quality slider:
  - Shown **only** when preset is `custom_quality`
  - Range: **1–95**
- Resize by percent:
  - Range: **10–200**
  - Aspect ratio preserved
- Blur <-> Sharpen slider:
  - Single centered slider (`-5.0` to `+5.0`)
  - Negative = blur, Positive = sharpen, `0.0` = neutral
- Contrast slider:
  - Range: **0.5–2.0**
- Brightness slider:
  - Range: **0.5–2.0**
- Output format conversion:
  - Convert output to **JPEG / PNG / WebP**
- Metadata handling:
  - Strip metadata toggle (default: enabled)
- Orientation:
  - Auto-orient via EXIF toggle (default: enabled)

### Output & UX
- True optimized output generated on the server and shown in UI.
- Before/After previews shown side-by-side.
- Download link for optimized output.
- Result line displays:
  - **Only changed properties** (no unchanged noise)
  - File-size change when changed
  - Dimension change when resized
  - Format change when converted
  - Brightness/Contrast/Blur-Sharpen values when adjusted
- Live parameter preview updates instantly when controls change (no heavy client-side processing).

---

## 4. Preset Quality Behavior (Current)
- `speed`: **30–50**
- `balanced`: **50–75**
- `max_quality`: **80–95**
- `custom_quality`: **1–95** (direct user control)

### Soft Clamp Rule
For non-custom presets, requested quality is softly clamped into the preset range.  
For `custom_quality`, the selected slider value is used directly within 1–95.

---

## 5. Architecture and File Structure

```text
flask app/
├── app.py
├── requirements.txt
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── extensions.py
│   ├── routes.py
│   └── utils/
│       ├── __init__.py
│       ├── validators.py
│       └── cleanup.py
├── templates/
│   └── index.html
├── static/
│   ├── css/styles.css
│   └── js/upload.js
└── temp/
```

### Responsibilities by Module
- `app.py`: runtime entrypoint (`create_app` + `app.run`)
- `app/__init__.py`:
  - app factory
  - config loading
  - extension init
  - blueprint registration
  - cleanup hook
  - 413 handler for oversized uploads
- `app/config.py`:
  - upload limits
  - allowed formats
  - defaults
  - quality bounds
  - temp storage settings
- `app/extensions.py`: Flask-Limiter setup
- `app/routes.py`: optimization endpoint and request processing pipeline
- `app/utils/validators.py`: strict upload validation logic
- `app/utils/cleanup.py`: scheduled/interval cleanup helper for temp files
- `templates/index.html`: UI layout
- `static/js/upload.js`: interaction logic and API calls
- `static/css/styles.css`: styling

---

## 6. Backend Request Flow (`/optimize`)
1. Receive multipart request containing:
   - image file
   - preset
   - quality
   - resize percent
   - output format
   - sharpness balance
   - contrast
   - brightness
   - metadata/orientation toggles
2. Validate file type and image integrity.
3. Parse and normalize control values.
4. Determine effective quality from preset rules.
5. Auto-orient if enabled.
6. Resize if requested (aspect ratio maintained).
7. Apply enhancement pipeline (blur/sharpen + contrast + brightness).
8. Apply encoder settings by output format + preset.
9. Return JSON containing:
   - optimized image data URL
   - output filename
   - input/output format
   - before/after file size
   - before/after dimensions
   - enhancement values used
   - effective quality and notes

---

## 7. Frontend Interaction Flow
1. User drops or selects an image.
2. Browser validates type quickly before request.
3. Before preview is shown immediately.
4. User adjusts preset/options.
5. Live parameter summary updates in-place.
6. On optimize:
   - POST request sent to `/optimize`
   - After image and download link updated from response
   - Change summary shows only what changed

---

## 8. Temp Data & Retention
- Current optimization response is returned directly (in-memory output path used by API response payload).
- Cleanup utility exists and is executed via app hook with interval + max-age controls.
- Temp folder structure is still present for operational flexibility and future workflows.

---

## 9. Dependencies
- Flask
- Flask-Limiter
- Pillow
- opencv-python-headless (present for future image/video enhancement work)

---

## 10. Local Development

### Environment
- Virtual environment path: `.venv`

### Run (PowerShell)
```powershell
.\.venv\Scripts\Activate.ps1
python app.py
```

### Default URL
- `http://127.0.0.1:5000`

---

## 11. Repository State
- Git repository initialized locally in project folder.
- Initial commit message: `initail application`

---

## 12. Known Improvement Opportunities
1. Add explicit server-side tests for preset mapping and dimension/size reporting.
2. Add background task queue for very large image workflows.
3. Add production rate-limit storage backend (Redis) for multi-instance deployment.
4. Add stronger UI formatting for size units (KB/MB) alongside bytes.


## SESSION 2:

Implemented advanced features

- Unified Blur <-> Sharpen control using a single slider (negative blur, positive sharpen)
- Contrast and Brightness sliders wired to Pillow enhancement pipeline
- Format Conversion - convert output between JPEG, PNG, and WebP via output format selector
- Result summary refined to show only changed values (size/dimensions/format/enhancements)

### Detailed implementation notes

#### 1. Backend changes (`app/routes.py`)
- Extended `/optimize` request parsing to accept:
  - `output_format`
  - `sharpness_balance`
  - `contrast`
  - `brightness`
- Added safe parsing helpers and bounds enforcement for new numeric controls.
- Added format validation to ensure only `JPEG`, `PNG`, `WEBP` are allowed as output.
- Added enhancement pipeline before encoding:
  - `sharpness_balance < 0` -> Gaussian blur with radius `abs(value)`
  - `sharpness_balance > 0` -> Pillow sharpness enhancement with mapped factor (`1.0` to `3.0`)
  - `contrast != 1.0` -> `ImageEnhance.Contrast`
  - `brightness != 1.0` -> `ImageEnhance.Brightness`
- Switched encoder path to use `output_format` instead of always preserving input format.
- Response payload now includes:
  - `input_format` and `output_format`
  - `sharpness_balance`, `contrast`, `brightness`
  - existing size/dimension/quality metadata

#### 2. Config updates (`app/config.py`)
- Removed split blur/sharpen defaults and ranges.
- Introduced single control defaults/range:
  - `DEFAULT_SHARPNESS_BALANCE = 0.0`
  - `SHARPNESS_BALANCE_RANGE = (-5.0, 5.0)`
- Kept existing contrast/brightness defaults and ranges.

#### 3. UI updates (`templates/index.html`)
- Replaced separate `Sharpen` and `Blur` sliders with one:
  - `Blur <-> Sharpen` slider (`-5` to `+5`, step `0.1`, default `0.0`)
- Added `Output format` selector (JPEG/PNG/WebP).
- Kept contrast and brightness sliders.

#### 4. Frontend behavior (`static/js/upload.js`)
- Updated DOM wiring for:
  - `sharpness_balance` slider/value label
  - output format selector
- Updated optimize request payload to send:
  - `output_format`, `sharpness_balance`, `contrast`, `brightness`
- Updated live parameter preview text to explain blur/sharpen directionality.
- Updated result summary generation to show only changed fields:
  - size change (when changed)
  - dimensions (when changed)
  - format conversion (when changed)
  - brightness/contrast/blur-sharpen (when non-default)

#### 5. UX behavior refinement
- Removed noisy always-on summary lines.
- Output now focuses on meaningful deltas only, making it easier to understand what the chosen settings actually changed.

## SESSION 3:

### Deployment update
- Deployed successfully on Render.
- Live app URL: https://flask-image-optimizer-60a9.onrender.com/
- Updated the Render startup command to use the Flask app factory in both deployment entrypoints:
  - `render.yaml`
  - `Procfile`
- Startup command now runs:
  - `gunicorn "app:create_app()" --bind 0.0.0.0:$PORT`