# F1-Simulation-

Predicts F1 Driver and Constructor champions using a multi-factor Monte Carlo model fed by real F1 data from FastF1.

## What This Software Predicts

- Current season Driver Champion
- Current season Constructor Champion
- Next season Driver Champion
- Next season Constructor Champion
- Title probabilities and expected points tables

## Factors Included

The simulator combines technical and external race factors:

- Engine performance
- Aero efficiency
- Chassis balance
- Mechanical grip
- Reliability and DNF risk
- Pit stop efficiency
- Strategy quality
- Tire management
- Driver pace, consistency, racecraft, adaptability
- Weather (wet and volatile race impact)
- Incident probability
- Team development rate
- Regulation adaptability (used for next-season projection)
- Qualifying position influence on race outcome
- Safety-car disruption effects
- Tire degradation pressure versus tire management
- Reliability sensitivity tuning and global chaos level

## How It Works

- Loads real race results, drivers, teams, and calendar from FastF1
- Simulates each race on a calendar with track-specific characteristics
- Applies weather and randomness for realistic race variability
- Scores each driver-team pairing for every race
- Awards F1-style points for top 10 finishers
- Repeats full seasons many times (Monte Carlo)
- Uses aggregated outcomes to estimate champion probabilities
- Projects team and driver growth/decline into the next season

## Run Locally

### Option 1: Quick Start (Windows)
Double-click `START_F1_SIM.bat` in the project folder. This will:
- Activate the virtual environment
- Start the Flask server on `http://localhost:8000`
- Open the browser automatically

### Option 2: Manual
```bash
# Activate virtual environment
.venv\Scripts\activate

# Install dependencies (if needed)
pip install -r requirements.txt

# Run the web app
python web_app.py
```

Then open `http://localhost:8000` in your browser.

---

## Deployment (Netlify + Render)

### Deploy Backend to Render

1. Push code to GitHub
2. Go to [render.com](https://render.com) and create account
3. Click "New Web Service"
4. Connect your GitHub repo
5. Configure:
   - **Name:** `f1-sim` (or your choice)
   - **Environment:** Python 3.11
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn web_app:app`
   - **Instance Type:** Free (or Starter)
6. Deploy
7. Copy your backend URL (e.g., `https://f1-sim-abc.onrender.com`)

### Deploy Frontend to Netlify

1. Update `public/index.html` line 173:
   ```javascript
   const BACKEND_URL = 'https://PASTE-YOUR-RENDER-URL-HERE';
   ```

2. Go to [netlify.com](https://netlify.com) and create account

3. **Option A: Drag & Drop**
   - Drag the `public/` folder onto Netlify
   - Done! Your site is live

4. **Option B: GitHub Auto-Deploy**
   - Connect your GitHub repo
   - Choose branch to deploy
   - Set build command to: `echo 'ready'`
   - Set publish directory to: `public`
   - Auto-deploys on each push

### API Endpoints

**Backend URL:** `https://your-render-url.onrender.com`

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | Landing page (local dev only) |
| `/simulation` | GET/POST | Form-based results (local dev only) |
| `/api/simulation` | POST | JSON API (used by Netlify frontend) |

**POST /api/simulation**
```json
{
  "simulations": 3000,
  "seed": 42,
  "top": 8,
  "year": "",
  "qualifying_weight": 0.28,
  "safety_car_rate": 0.26,
  "tire_impact": 0.32,
  "reliability_sensitivity": 0.30,
  "chaos_level": 0.35
}
```

Response: Championship predictions with probabilities and expected points

---

### Project Structure

```
F1-Simulation-/
├── app.py                    # Core prediction engine
├── main.py                   # CLI interface
├── web_app.py                # Flask API server (backend)
├── requirements.txt          # Python dependencies
├── netlify.toml              # Netlify configuration
├── START_F1_SIM.bat         # Quick start script (Windows)
├── public/                   # Static frontend (for Netlify)
│   ├── index.html           # Frontend with API integration
│   └── styles.css           # Stylesheet
├── templates/               # Flask templates (local dev)
│   ├── landing.html
│   └── index.html
├── static/                  # Static assets (local dev)
│   └── styles.css
└── README.md
```

---

### Architecture

**Local Development:**
```
Browser → Flask App (localhost:8000) → Predictions
           ↓
        templates/ + static/
```

**Production (Netlify + Render):**
```
Browser → Netlify Frontend (netlify.app) → Render Backend (onrender.com)
          (public/index.html)                 (web_app.py)
                                              → Predictions
```

Optional arguments:

```bash
python main.py --simulations 5000 --seed 7 --top 8
```

Advanced options:

```bash
python main.py --year 2025 --qualifying-weight 0.35 --safety-car-rate 0.30 --tire-impact 0.40 --reliability-sensitivity 0.45 --chaos-level 0.50
```

- `--simulations`: number of simulated seasons (minimum effective floor: 200)
- `--seed`: random seed for reproducible results
- `--top`: how many top rows to display in each summary table
- `--year`: explicit season year to load from FastF1 (default: latest available)
- `--qualifying-weight`: grid-position impact on race performance (0.0 to 1.0)
- `--safety-car-rate`: frequency of safety-car style disruptions (0.0 to 1.0)
- `--tire-impact`: tire degradation influence (0.0 to 1.0)
- `--reliability-sensitivity`: reliability impact on DNF risk (0.0 to 1.0)
- `--chaos-level`: randomness and incident intensity (0.0 to 1.0)

## Web Dashboard

Install dependencies:

```bash
pip install -r requirements.txt
```

Start the interactive dashboard:

```bash
python web_app.py
```

Then open:

```text
http://127.0.0.1:8000
```

Dashboard features:

- Interactive controls for simulations, seed, and table length
- Season year selector and advanced factor controls
- Current season champion and standings forecast
- Next season projected champion and standings forecast
- Visual probability bars for title outcomes

## Data Source

- Primary source: FastF1 (real F1 schedule and race results)
- The simulator auto-selects the most recent season that has available completed race results
- FastF1 cache is stored in `.fastf1_cache/` to speed up subsequent runs
- If FastF1 data is temporarily unavailable, the app falls back to built-in sample data

## Files

- `app.py`: simulation engine and prediction logic
- `main.py`: CLI runner and formatted output
- `web_app.py`: Flask web dashboard entry point
- `templates/index.html`: dashboard page template
- `static/styles.css`: dashboard styling
