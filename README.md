# CrisisCompass: Location-Based Emergency Monitoring System

**CrisisCompass** is a web application that uses your browser location to drive **server-side** news aggregation and keyword-based severity ranking. The dashboard shows a ranked list of incidents with trust heuristics; the heaviest work (scraping, NLP, scoring) runs on the **backend**, not in the browser.

---

## **Features**

- **Automatic location detection**: Browser geolocation supplies coordinates to the API for regional feed queries
- **Local news monitoring**: Backend fetches RSS and related sources for your area
- **Severity ranking**:
  - Keyword scoring with word boundaries, light negation handling, and stronger weight for headline matches than body-only matches
  - Trust score adjustments from trust-related terms
  - Ranked list with more severe items first
- **Dashboard**:
  - Severity shown with **icons and text** (not color alone)
  - Source name and article link on each card when a URL is available
- **Development workflow**: Single `npm run dev` starts Flask and Vite together, with the frontend calling `/api/...` through a Vite proxy

---

## **Technologies Used**

### Backend

- **Python**: Flask, Flask-CORS, BeautifulSoup, spaCy, feedparser, geopy, requests

### Frontend

- **React** (Vite), **Tailwind-related tooling** (PostCSS), **Lucide React**, **Axios**
- **Vite dev proxy**: `/api` → `http://127.0.0.1:5000` (override with `VITE_DEV_API_PROXY_TARGET` if needed)

---

## **Setup**

### Prerequisites

- Python 3.9+
- Node.js (v18+ recommended)

### Quick setup

1. **Clone the repository** and enter the project directory.

2. **Backend** (from project root — the script `cd`s into `backend`):

   ```bash
   python setup_backend.py
   ```

3. **Frontend**:

   ```bash
   npm install
   ```

4. **Run app (Flask + Vite)**:

   ```bash
   npm run dev
   ```

5. Open **http://localhost:5173** (or the URL Vite prints).

### Optional environment

| Variable | Purpose |
|----------|---------|
| `VITE_API_URL` | API base path or origin for the browser (default: `/api` so the dev proxy is used) |
| `VITE_DEV_API_PROXY_TARGET` | Backend URL for the Vite proxy (default: `http://127.0.0.1:5000`) |
| `CRISIS_COMPASS_DEV_SAMPLES` | Set to `1` / `true` / `yes` to inject **labeled dev-only sample incidents** when all feeds return nothing |
| `CRISIS_COMPASS_DB_PATH` | Optional absolute path to the SQLite file (default: `backend/data/crisis_compass.db`) |
| `OPENAI_API_KEY` | Optional; enables **Reports** AI summary and entity graph (LangChain + OpenAI). Easiest: put it in a **`.env`** file in the project root (copy from `.env.example`); the Flask app loads it automatically via `python-dotenv`. |
| `OPENAI_REPORT_MODEL` | Optional OpenAI model id for reports (default: `gpt-4o-mini`) |

### Manual backend (optional)

```bash
cd backend
pip install -r requirements.txt
python -m spacy download en_core_web_sm
python app.py
```

---

## **How It Works**

1. The browser requests location permission and sends coordinates to `POST /get-local-incidents`.
2. The **server** reverse-geocodes, selects feeds, fetches and parses articles, and scores text.
3. Incidents are **deduplicated** by URL (or title+location), merged into an in-memory cache, and **persisted to SQLite** (default path under `backend/data/`, gitignored) for reporting windows and exports.
4. The React app loads data via **`/api/...`**, so production can serve API and UI from one host by setting `VITE_API_URL` appropriately.
5. **Reports** uses deterministic aggregates from stored incidents; optional **LangChain** narrative and entity graph run only when `OPENAI_API_KEY` is set on the server.
6. **Settings** (severity floor, quiet hours, AI toggles, accessibility) are stored in **localStorage** in the browser.

---

## **API Endpoints**

- `GET /get-incidents` — Stored incidents (deduplicated)
- `POST /get-local-incidents` — Body: `{ "latitude", "longitude" }` — fetch and merge regional incidents
- `POST /scrape` — Manual URL scrape (legacy)
- `GET /report/summary?hours=24&compare_hours=` — JSON aggregates (optional `compare_hours` for previous window)
- `GET /report/export.csv?hours=24` — CSV export for the window
- `GET /report/print.html?hours=24` — Printable HTML summary (use browser Print to PDF)
- `POST /report/insights` — Body: `{ "hours", "compare_hours", "include_llm", "tone", "length" }` — summary + optional AI fields

---

## **Privacy & Security**

- Coordinates are sent to **your backend** for geocoding and feed selection. Incident text and metadata are stored in **local SQLite** on the server (for the dashboard and reports); review retention and disk on your deployment.
- News fetching follows normal HTTP and feed semantics; respect site terms and rate limits in production.
- **Analysis and scraping run on the server**, not inside the user’s browser.
