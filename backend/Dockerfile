# Image for the Python backend (FastAPI).
FROM python:3.12-slim

WORKDIR /app

# Install libraries first so Docker can reuse this step when only code changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
# --reload restarts the server automatically when you save a .py file.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
