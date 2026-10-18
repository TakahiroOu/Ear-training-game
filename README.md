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

After adding a new library (`npm install ...` or a new line in `requirements.txt`), rebuild with:

```
docker compose up --build -V
```

(`-V` makes Docker reinstall the libraries instead of reusing the old ones.)

To play on your phone: connect it to the same Wi‑Fi, find your PC's IP address with `ipconfig`
(the "IPv4 Address", e.g. 192.168.1.20), and open `http://192.168.1.20:5173`.
If it doesn't load, allow Docker / port 5173 in the Windows Firewall.

## Tests

```
docker compose exec backend pytest     # Python: music logic + API
cd frontend && npm test                # JavaScript: game rules
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
