# Ear Training Web App — Project Plan

## Context

You built a working ear-training game in Python/pygame ([main.py](../main.py)):
- 36 piano samples C3–B5 in `sounds/`, plus `right_answer.wav` / `false_answer.wav`
- Modes 1–4: one note, two notes, a major/minor triad, a 7th chord (dom7 / min7), each note moved to a random octave
- The player clicks piano keys, presses ENTER to check and SPACE to replay. Correct answers add +1…+4 points and wrong ones add +4…+1 mistakes. The first side to reach 50 wins or loses.

**The problem:** pygame only runs on a desktop where Python is installed, so nobody can play it in a browser or on a phone.
**The goal:** turn it into a web app that anyone can open in a browser. Later it adds accounts, stats, difficulty levels, intervals and chords, an **entrance-exam mode** for students applying to a music conservatory (many notes at once), and **competitions**. After that it can be packaged as a phone app.

---

## 1. Technology stack and why each piece is used

| Layer | Technology | Why |
|---|---|---|
| What the player sees (frontend) | **React + JavaScript** | Browsers only run JavaScript, so a web game *must* use JS, and Python can't run there. React lets you build the screen from small reusable pieces ("components") like `<Piano>`, `<Key>` and `<ScoreBoard>`. Your `MakePiano.draw_piano()` becomes a `<Piano>` component. React redraws a key automatically when its state changes (e.g. clicked → blue), so you don't need a manual redraw loop like `main_loop`. |
| Playing sounds | **Tone.js** (built on the browser's Web Audio API) | It replaces `pygame.mixer`. It loads your WAV/MP3 samples and plays several notes at **exactly** the same moment, which chords need. You can ask it for notes by name (`"C#4"`). |
| Development tools | **Node.js + npm + Vite** | Node runs JavaScript *outside* the browser. Here it isn't the game server. It powers the dev tools: `npm` installs libraries (like `pip`), and `Vite` runs a dev server that reloads instantly when you save. It also bundles your code for production. |
| Server / API (backend) | **Python + FastAPI** | You already know Python, so you can reuse your music logic (`make_octave`, `make_3notes`, …) almost as-is, without pygame. The server creates questions, grades competition answers (so nobody can cheat by editing browser code), and manages accounts and scores. FastAPI is modern, fast, simple, and generates an interactive API test page at `/docs` automatically. |
| Data storage | **Supabase** (hosted **PostgreSQL**) + **SQLAlchemy** (Python ↔ SQL) + **Alembic** (database changes over time) | SQL *is* necessary once you have users, scores, leaderboards and competitions. That data is naturally tables with relationships (a user has many game sessions, and a competition has many entries). SQL makes queries like "top 10 scores this week" one short statement. Supabase runs a real PostgreSQL database for you with automatic backups and HTTPS, and the free tier is enough for this project. Because it's normal Postgres, SQLAlchemy and Alembic work unchanged, and you could move to any other Postgres host later. |
| Login / accounts | **Supabase Auth** | Sign-up, login, password hashing, email confirmation, password reset, and later "Sign in with Google". Writing these yourself is where beginners most often create security holes, so a well-tested service is **safer**. The browser logs in through Supabase and gets a token, and FastAPI checks that token on every request. |
| Running everything | **Docker + Docker Compose** | The React dev server and the Python API each need their own setup. Docker puts each in a "container" with everything installed, and `docker compose up` starts them together with one command. It runs the same way on your PC, a friend's PC, or a cloud server. A small local Postgres container is used **only for automated tests**, so tests never touch real data. |
| Phone app (later) | **PWA → Capacitor** | See section 4. You reuse the *same* React code for the phone app. |

**How the parts talk to each other:**
```
Browser (React + Tone.js)  ──HTTP/JSON + login token──▶  FastAPI (Python)  ──SQL──▶  Supabase Postgres
   plays sounds, draws piano                            makes questions, grades,     users, scores,
        │                                               checks token, leaderboards   competitions
        └──── login only ────▶  Supabase Auth  (gives the browser a login token)
```

**Safety rule:** the browser only uses Supabase to **log in**. It never reads or writes database tables directly, and all data goes through FastAPI. That keeps competition grading cheat-proof. It also avoids Supabase's most common security mistake: tables the public can read or change because "Row Level Security" was left off. As an extra safety net, Row Level Security is still **turned on for every table** with no public policies. FastAPI connects with the server-side database password, which is never put in frontend code.

---

## 2. Project folder structure

```
ear-training-app/
├── docs/PLAN.md                 ← this plan
├── README.md                    ← how to run the project
├── docker-compose.yml           ← starts frontend + backend (+ test database)
├── .env.example                 ← template for Supabase URL / keys / DB password (real .env is git-ignored, never committed)
├── legacy/                      ← your original pygame game, kept for reference
│   └── main.py
├── frontend/                    (React, JavaScript, Node tooling)
│   ├── Dockerfile
│   ├── package.json
│   ├── public/sounds/           ← piano samples converted to .mp3 (WAVs total ~20 MB, too big for web)
│   └── src/
│       ├── main.jsx, App.jsx
│       ├── components/  Piano.jsx, Key.jsx, ScoreBoard.jsx, ModeSelector.jsx, RulesScreen.jsx, GameOver.jsx
│       ├── audio/       sampler.js     ← Tone.js wrapper (replaces AudioCreator's sound loading)
│       ├── game/        useGame.js     ← game state: score, mistakes, selected keys (replaces class Game)
│       ├── api/         client.js      ← calls to the backend
│       └── pages/       Play, Login, Stats, Leaderboard, Competition
└── backend/                     (Python)
    ├── Dockerfile
    ├── requirements.txt
    ├── app/
    │   ├── main.py              ← FastAPI app + routes
    │   ├── music.py             ← YOUR logic ported: note names, make_octave, chord/interval generators
    │   ├── models.py            ← SQL tables (SQLAlchemy)
    │   ├── schemas.py           ← request/response shapes (Pydantic)
    │   ├── auth.py              ← checks the Supabase login token, finds the current user
    │   └── routers/  questions.py, users.py, sessions.py, competitions.py
    ├── alembic/                 ← database migration scripts
    └── tests/  test_music.py, test_api.py
```

The existing `sounds/` folder becomes `frontend/public/sounds/` after conversion. The empty `main.css` is replaced by the frontend's styles, and `images/` moves to `frontend/public/images/`.

---

## 3. Roadmap (build in phases, each phase gives you something that works)

### Phase 0 — Setup (learning the tools) ✅ finished
- Install: Node.js LTS, Python 3.12, Docker Desktop, VS Code extensions (ES7 React, Python).
- Move `main.py` → `legacy/main.py`. Create `frontend/` with `npm create vite@latest frontend -- --template react`. Create `backend/` with FastAPI.
- Convert WAV → MP3 with `ffmpeg` (a small script), about 20 MB down to about 2 MB.
- Write `docker-compose.yml` with 2 services: `frontend` (port 5173) and `backend` (port 8000). There's no database yet, because Phase 1 doesn't need one.
- ✅ Done when `docker compose up` shows the React start page and `localhost:8000/docs` shows FastAPI.

### Phase 1 — Your current game, in the browser ✅ finished
Also fixed from the pygame version: ENTER before any question gave free points, and pressing ENTER again after a correct answer scored the same question again.
- **Backend** `music.py`: port `AudioCreator`'s logic without pygame, working with note *names/indices* only:
  - `NOTE_NAMES` (C3…B5), `make_octave(index)`, `make_1note()`, `make_2notes()` (keeps your "not adjacent" rule), `make_3notes()` (major/minor triad), `make_4notes()` (dom7/min7).
  - Route `GET /api/questions?mode=3` → `{"notes": ["E3","G#4","B4"]}`.
- **Frontend**:
  - `<Piano>`: 21 white + 15 black keys drawn with HTML/CSS (same layout as `draw_piano`), colored white/black → blue (selected) → green/red after checking.
  - `sampler.js`: load the 36 samples with Tone.js and play a list of notes together.
  - `useGame.js`: points / mistakes / current mode and the same scoring rules (+mode for correct, +(5−mode) for wrong, 50 wins/loses).
  - Keyboard shortcuts as before (1–4, ENTER, SPACE) **plus on-screen buttons** so it works on touch screens.
  - Rules screen and win/lose screen.
- Improvement over the original: when the answer is wrong, show the correct keys in red/green. Your code has a `showing_correct` flag, but it's never used.
- **Ready for two languages:** all text shown to players lives in `src/i18n/` (`en.js`, `ja.js`) instead of being written directly in components. Adding Japanese/English later (important for search engines, see section 5) then needs no component changes.
- ✅ Done when the full game plays in Chrome and on your phone's browser over Wi‑Fi.

### Phase 2 — Accounts, saved progress, stats (SQL arrives, with Supabase) ✅ finished
- **Set up Supabase**: create a free account and **two projects**: `ear-training-dev` (for experimenting) and later `ear-training-prod` (real users). Put each project's URL, public "anon" key and database connection string in `.env`. The secret `service_role` key and the DB password stay **only** in the backend's `.env`. Never put them in frontend code or commit them to git.
- **Login**: the frontend uses `@supabase/supabase-js` *only* for sign up / log in / log out / password reset. It sends the login token to FastAPI with each request, and `auth.py` verifies the token (JWT) and gets the user id. Guests can still play without an account.
- Tables (created with Alembic migrations from the backend):
  - `profiles` (id = Supabase user id, username, created_at). Supabase stores emails and passwords itself in `auth.users`, so **you never handle passwords**.
  - `game_sessions` (id, user_id, mode, points, mistakes, result, started_at, ended_at)
  - `answers` (id, session_id, question_notes, given_notes, correct, response_ms) → powers "which notes do I miss most?"
- **Security checklist**: Row Level Security is ON for every table, and the Supabase dashboard's "Security Advisor" shows no warnings. Email confirmation is on.
- **Development database runs locally** (the `db` service in Docker Compose). The development computer's network blocks direct database connections to the internet, while Supabase *login* (HTTPS) works. So during development: logins come from the Supabase project `ear-training-dev` (Tokyo), and data is stored in the local `db`. Once online (Phase 6), `DATABASE_URL` points to the Supabase database, and migrations run from the server.
- **Tests** use a throwaway local Postgres container (`db-test` service in Docker Compose), so tests never touch Supabase data.
- Stats page: accuracy per note and per mode, streaks, a history chart (Recharts).
- ✅ Done when a logged-in user's history survives a browser refresh and a server restart.

### Phase 3 — Exam course: Tokyo Geidai (東京藝大) dictation 🎓 the main paid product
**What the exam tests** (from Geidai's official exam guides for 2020–2022 and teachers' write-ups; **always re-check the newest official guide**): a written dictation test (聴音書き取り) of about 30 minutes with three parts:
1. **Single melody (単旋律)**. From the 2026 entrance year it is reportedly a **memory dictation (記憶聴音)**: listen first, then write it down.
2. **Two-voice piece (複旋律 / 2声)**.
3. **Four-part harmony (四声体和声)**: chord progressions, with modulations to distant keys in the harder parts.

Questions usually start easier and get harder toward the end. Sight-singing (新曲視唱) and music theory (楽典) are also tested; they can be added later as extra modules.

**Research first, without copying** (step 3a):
- Collect the **official guides and past exams** from [Geidai's admissions site](https://admissions.geidai.ac.jp/data/past-exams/music/) and look through popular exam workbooks.
- Write `docs/exam-syllabus.md`: for each part, the length (bars), keys, time signatures, note values, intervals, chords and modulations that appear, from easy to exam level. Split it into **STEP 1–9**, like the Senzoku 810 site.
- Use books and past exams only to *learn what is tested*. **Never copy their melodies or exercises**, because they are copyrighted. All exercises in the app are **generated by our code** or **newly composed**.
- Later, ask a teacher or a recent Geidai student to review the syllabus. There's no exam experience on the team yet, so outside review matters.

**New features needed** (step 3b onwards):
- **Staff notation**: draw music on a staff with **VexFlow** (a JavaScript library), for both the student's answer and the correct answer.
- **Answer input**: choose the pitch on the piano keyboard (already built) and the length with buttons (whole, half, quarter, eighth, sixteenth, dotted, rest, tie). Each note appears on the staff as you enter it.
- **Grading note by note and bar by bar**, showing the mistakes in red and a score like the exam.
- **Exercise generators** in Python (`backend/app/exam/`): melodies that follow musical rules (stepwise motion, sensible leaps, cadences), two-voice counterpoint, and four-part chorale progressions (I–IV–V–I, secondary dominants, modulations) by STEP. Every generated exercise gets unit tests (e.g. "the voices never cross", "ends on a cadence").
- **Exam-style playback**: the same way the exam plays it (number of plays, pauses, tempo, starting note / key given), plus memory-dictation mode.
- **Mock exams**: the full 30-minute, three-part test, timed, with a score report.

**Course structure:**
| Course | For | Price |
|---|---|---|
| 🎮 Casual game | Anyone, for fun (the Phase 1 game + Phase 4 modes) | Free |
| 🏆 Competition | Ranking and rivals (Phase 5) | Free |
| 🎓 Exam course: **1 / 3 / 6 months** | Conservatory applicants, Geidai first | **Paid** |

- At the start: a **placement test** decides the starting STEP. The student enters their **exam date**, and the app builds a **daily plan** that ends in exam-level mock tests.
- 1 / 3 / 6 months = the same content at different speeds. 6 months starts from basics, and 1 month is an intense review.
- Progress page: score per part, weak points (e.g. "you often miss minor 6ths", "rhythm in bar 3–4"), and a chart of mock exam scores.
- **Why pay when Senzoku 810 is free?** Automatic grading, endless new exercises, a plan up to the exam date, weak-point analysis, Geidai-format mock exams, and it works well on phones.

New tables: `courses`, `enrollments` (user_id, course, plan_months, exam_date, start_step, started_at), `exercises` (id, type, step, seed, data), `exercise_attempts` (user_id, exercise_id, answer, score, created_at).

### Phase 4 — More game modes and difficulty levels (casual course)
- **Difficulty levels**: (1) white keys in one octave → (2) all 12 notes, one octave → (3) 3 octaves (current game) → (4) wider range. Unlocked by accuracy.
- **Intervals mode**: two notes, answer by *name* (m3, P5, …) with answer buttons instead of the piano. Melodic (one after another) or harmonic (together).
- **Chord quality mode**: major / minor / diminished / augmented / dom7 / maj7 / min7, plus inversions.
- **Many notes at once**: 4–6 notes (clusters and chords in any voicing), graded per note.
- All generators live in `backend/app/music.py` with unit tests (e.g. "a minor triad is always root, +3, +7 semitones").
- New table `user_progress` (user_id, mode, level, best_accuracy).

### Phase 5 — Competitions
- All competitions are **free to enter** (see section 5 for why there are no paid entries).
- **Daily challenge**: everyone gets the *same* 20 questions each day (generated from a seed such as the date). The score uses accuracy and speed. There's a daily and an all-time leaderboard.
- **Weekly and monthly contests**: longer question sets with fixed start and end times. Winners get rankings, badges, titles and a "hall of fame" page. Later, prizes may come from sponsors (see section 5).
- **Server-side grading**: in competition mode the browser receives the sounds to play but *not* the answer, and the server checks each answer. This prevents cheating.
- **Class competitions** (good for music schools): a teacher creates a competition with a join code, students join, and a leaderboard for that group appears.
- Tables: `competitions` (id, name, type, seed, starts_at, ends_at, join_code, created_by), `competition_entries` (competition_id, user_id, score, time_ms).
- *Optional later*: live 1‑vs‑1 battles over WebSockets (FastAPI supports them).

### Phase 6 — Go online
- Use production Docker images (`npm run build` → static files served by Nginx, `uvicorn` for the API).
- Simplest hosting for the two containers: **Render** or **Railway** (they run Docker containers; small projects start free or cheap). Alternative: one small VPS running `docker compose`. The database and login stay on Supabase (`ear-training-prod` project).
- HTTPS is automatic on those hosts and on Supabase. Secrets go in the host's environment-variable settings. Supabase makes daily backups. Note that **free Supabase projects pause after about a week with no activity**, so upgrade to the paid plan once real users depend on it.
- GitHub Actions: run backend tests and the frontend build on every push. Your repo is already on GitHub at TakahiroOu/Ear-training-game.

### Phase 7 — Be found on Google (SEO)
- **Landing pages built ahead of time** (static HTML that Google can read, not only the JavaScript game): home, one page per mode, a "conservatory entrance-exam preparation" page, and the contest hall of fame. Each page gets its own title, description and share image.
- **Japanese and English versions** of each page, with `hreflang` tags so Google shows the right language.
- **Content that answers what people search for**, e.g. 「聴音 練習」「音大受験 聴音 対策」「和音 聞き取り」「絶対音感 トレーニング」, "ear training chords", "interval ear training". Each page includes a free mini-trainer.
- **Technical basics**: fast loading, works well on phones, `sitemap.xml`, `robots.txt`, structured data (schema.org), and **Google Search Console** + Bing Webmaster Tools to see which searches bring people.
- **Links from other sites**: tell music teachers, schools and YouTube creators about the app. Class competitions spread through teachers. Add a "share your result" button. No bought links, because Google penalizes them.
- **App Store Optimization** once the phone apps exist: name, keywords and screenshots in both languages.

### Phase 8 — Subscription
- Free: the casual game and competitions. Paid: the **exam course as 1 / 3 / 6-month plans** (Phase 3). Other paid extras will be decided together later.
- Also consider a **family plan** (parents pay for children) and a **teacher / school plan** (one payment for a whole class).
- Web payments with **Stripe** (Stripe Checkout + Customer Portal; the backend listens to Stripe "webhooks" to switch a user's plan on and off). Card numbers never touch our server.
- Phone apps: Apple / Google in-app purchase rules apply (they take 15–30%). One user account works with both web and app subscriptions.
- New table: `subscriptions` (user_id, plan, status, provider, current_period_end).

### Phase 9 — Phone app
See section 4.

### Phase 10 — Ads (optional)
- **Google AdSense** on the website, **AdMob** in the phone app. Only for free users, with **subscribers seeing no ads**.
- Ads only in quiet places (results screen, menus). Never ads that play sound during listening exercises.
- Child-safe ad settings if users under 13 are expected.
- Expect small income (a few hundred yen per 1,000 page views), so ads mainly push users toward subscribing.

---

## 4. Is it easy to make both a web version and a phone app? Yes, if you plan for it now

Because the game is built in React, you can reuse almost all of it:
1. **PWA (Progressive Web App)**: add a manifest + service worker (`vite-plugin-pwa`). Users tap "Add to Home Screen" and it opens like an app with an icon, full screen, and sounds cached offline. *A few hours of work.*
2. **Capacitor**: wraps the same React build into real **Android and iOS apps** you can publish to Google Play and the App Store. *Mostly configuration, with almost no code changes.*
   - Android: Google Play account ($25 once). iOS: Apple Developer account ($99/year), and building requires a Mac (or a cloud Mac build service).

Rules to follow from Phase 1 so this stays easy:
- Design for touch: big keys, on-screen buttons for everything that has a keyboard shortcut, and a layout that works at phone width (the piano scrolls or shows fewer octaves on small screens).
- Start audio only after the first tap. Phones block sound until the user interacts, and Tone.js handles this with `Tone.start()`.
- Keep all server calls in `api/client.js` with a configurable server URL.

(Not recommended: rewriting the app in React Native or Flutter. That means writing a second app, which isn't worth it for this game.)

---

## 5. Growth & money — decisions and reasons

| Idea | Decision | Why |
|---|---|---|
| Free competitions (daily / weekly / monthly) | ✅ Yes | Brings users back regularly and spreads the app through schools. |
| **Paid entry with cash prizes** | ❌ No, at least for now | (1) Entry fees paid into a prize pot can count as **gambling** in many countries, and Japan is strict. (2) In Japan, even prizes you fund yourself are **capped by the prize law (景品表示法)** if only paying users can enter. (3) Many users are **minors** (conservatory applicants). (4) **Cheating can't be stopped**: a free pitch-detection app on a second phone names every note. (5) Apple and Google allow real-money contests only with licenses and in some countries. |
| Prizes for contests | ⏳ Later, maybe | Only with **free entry** and prizes paid by us or a **sponsor** (music shops, instrument brands, exam-prep schools). **Ask a lawyer first.** |
| Subscription (freemium) | ✅ Yes, Phase 8 | The standard and most reliable income for learning apps. |
| Ads | ✅ Optional, Phase 10 | Low income unless traffic is large, and they can disturb listening. Use as "free with ads, subscribe to remove them". |
| SEO | ✅ Yes, Phase 7 | Nobody can guarantee the #1 spot, but useful bilingual pages, technical basics and links from teachers and schools are what work. |

Legal notes are warnings, not legal advice. Rules depend on the country, so check with a professional before taking money from users or giving prizes.

---

## 6. Verification (how to check each phase works)
- `docker compose up --build`, then open `http://localhost:5173` (game) and `http://localhost:8000/docs` (try the API in the browser).
- Backend tests: `docker compose exec backend pytest`. They check the chord generators, octave range (always within C3–B5), scoring, and the login flow.
- Frontend: `npm run build` must succeed, and you play each mode manually on desktop Chrome and on a phone over the local network.
- Phase 2 and later: restart the containers and confirm users and scores are still there (they live in Supabase, not in the containers). Security check: try to read a table with only the public anon key, for example with `supabase-js` in the browser console. It must return nothing.

## 7. Order of work
Phases are numbered in build order: 2 (accounts) → 3 (exam course) → 4 (more game modes) → 5 (competitions) → 6 (online) → 7 (SEO) → 8 (subscription) → 9 (phone app) → 10 (ads).
The exam course comes early because it is the paid product, but it only earns money after going online (6) and adding payments (8).
