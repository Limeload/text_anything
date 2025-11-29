## Text Anything – Coding Challenges

This repository contains two independent, production-style Python projects:

- **Challenge 1:** Geofence Event Processing Service (`geofence_service/`)
- **Challenge 2:** Leaderboard Points Ranking System (`leaderboard_ranker/`)

---

## Challenge 1 – Geofence Event Processing Service

**Tech stack:** Python, FastAPI, Uvicorn, Pydantic  
**Path:** `geofence_service/`

**Purpose:**  
Process real-time GPS events, detect **ENTER / EXIT / CHANGE** transitions for rectangular zones, and keep in-memory vehicle state.

**Key features**
- Endpoints:
  - `POST /events/location` – ingest GPS events
  - `GET /vehicles/{vehicleId}/status` – current zone, last location, transitions
  - `GET /zones` – debug view of zones + current vehicle counts
  - `GET /health` – basic health check
  - `GET /` – simple service info + links
- Zones loaded from `geofence_service/zones.json` (rectangular bounds: `min_lat`, `max_lat`, `min_lng`, `max_lng`)
- GPS cleaning:
  - `"D$Q"`, `"-"`, `""`, `NaN`, `None`, `"NULL"`, etc. → treated as `0.0`
  - Out-of-range coordinates are normalized to `0.0`
- In-memory state tracking:
  - Per-vehicle last location, current zone, and transition history
  - Per-zone live vehicle counts
- Pydantic models, logging, and exception handling
- Unit tests in `geofence_service/tests/`

**How to run**

```bash
cd /Users/shraddharao/Development/code/Work/text_anything
python3 -m venv .venv
source .venv/bin/activate

cd geofence_service
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Then open:
- Swagger docs: `http://127.0.0.1:8000/docs`
- Health check: `http://127.0.0.1:8000/health`
- Root info: `http://127.0.0.1:8000/`

For more details (assumptions, architecture, scalability, improvements), see `geofence_service/README.md`.

---

## Challenge 2 – Leaderboard Points Ranking System

**Tech stack:** Python, Pandas, NumPy, OpenPyXL  
**Path:** `leaderboard_ranker/`

**Purpose:**  
Read a leaderboard Excel file, clean values, compute ranking metrics, and sort players by:

1. **Total points** – descending  
2. **Spend** – ascending  
3. **Countback** – descending (highest score + frequency, then next highest, etc.)  
4. **Alphabetical** – player name as final fallback  

**Key features**
- Reads `leaderboard_ranker/leaderboard.xlsx`
- Cleans invalid values:
  - `"D$Q"`, `"–"`, `"-"`, `NaN`, `None`, `"N/A"`, `"NULL"`, etc. → `0.0`
  - Strips currency symbols / non-numeric characters
- Builds full per-event score list per player
- Computes:
  - `total_points`
  - `spend`
  - `countback` tuple
  - `median_score` (documented as a suggested extra tiebreaker)
- Sorts using the required priority rules
- Outputs **three files to the project root**:
  - `leaderboard_sorted.csv`
  - `leaderboard_sorted.xlsx`
  - `leaderboard_sorted.json`
- Simple CLI: `python rank.py`

**How to run**

```bash
cd /Users/shraddharao/Development/code/Work/text_anything
source .venv/bin/activate   # reuse the same venv

cd leaderboard_ranker
pip install -r requirements.txt
python rank.py
```

This will read `leaderboard_ranker/leaderboard.xlsx` and write the sorted outputs into the project root (one directory up).

For more details (data cleaning, sorting rules, countback algorithm, example tie resolution, and suggested median-score tiebreaker), see `leaderboard_ranker/README.md`.

# text_anything
