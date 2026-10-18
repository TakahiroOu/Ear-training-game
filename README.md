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

## Accounts and the database (Supabase)

Without setup, everyone plays as a guest. To turn on accounts and saved progress:

1. Copy `.env.example` to `.env` and fill in the values from your Supabase project
   (the comments in the file say where to find each one). `.env` is never committed.
2. Restart: `docker compose up -d --force-recreate`
3. Create the tables in Supabase: `docker compose exec backend alembic upgrade head`

When a table changes later, a new file is added in `backend/alembic/versions/`, and step 3 applies it.

## Online (Render + Supabase)

- `render.yaml` describes the two online services: the website (free static site) and the API
  (free Docker web service in Singapore, built from `backend/Dockerfile.prod`).
- Every push to `main` is deployed automatically. The API runs the database migrations when it starts.
- Secrets (database password etc.) are typed into Render's dashboard only, never into the code.
- GitHub runs all tests on every push (`.github/workflows/tests.yml`).

## Tests

```
docker compose exec backend pytest     # Python: music logic, API, saving games, login checks (uses a throwaway test database)
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
