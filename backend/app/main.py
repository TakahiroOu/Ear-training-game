from fastapi import FastAPI

app = FastAPI(title="Ear Training API")


@app.get("/api/health")
def health():
    """Lets the frontend (and you) check that the backend is running."""
    return {"status": "ok"}
