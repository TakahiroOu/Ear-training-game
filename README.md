# Ear Training Game

A music ear-training game: listen to one or more notes, then pick them on the piano keyboard.

See the full roadmap and the reasons behind each technology in [docs/PLAN.md](docs/PLAN.md).

## Run the web app (in development)

Needs Docker Desktop running.

```
docker compose up --build
```

- Game (React): http://localhost:5173
- API test page (FastAPI): http://localhost:8000/docs

Stop it with `Ctrl+C`, or `docker compose down` if it runs in the background.

Run the backend tests:

```
docker compose exec backend pytest
```

## Project layout

| Folder | What's inside |
|---|---|
| `frontend/` | React app (JavaScript, built with Vite) |
| `backend/` | Python API (FastAPI) and its tests |
| `scripts/` | Helper scripts, e.g. `convert_sounds.py` (WAV → MP3 for the web) |
| `sounds/` | Original WAV piano samples |
| `legacy/` | The original pygame version of the game |
| `docs/` | Project plan |

## Run the original pygame version

From the project folder:

```
pip install pygame
python legacy/main.py
```
