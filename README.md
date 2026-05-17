# Image Optimiser (Flask)

A Flask web app for interactive image optimization with before/after preview and downloadable output.

## Features

- Drag-and-drop upload flow
- Strict validation for JPEG/PNG/WebP
- Presets: `speed`, `balanced`, `max_quality`, `custom_quality`
- Custom quality, resize %, blur↔sharpen, contrast, brightness controls
- Optional metadata stripping and EXIF auto-orient
- Output format conversion to JPEG/PNG/WebP
- JSON response with size/dimension/quality summary

## Tech Stack

- Flask
- Flask-Limiter
- Pillow
- OpenCV (headless)

## Run Locally (PowerShell)

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Open: `http://127.0.0.1:5000`

## Tests

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test*.py"
```

## Deployment

- `Procfile` and `render.yaml` are included for Render deployment.
