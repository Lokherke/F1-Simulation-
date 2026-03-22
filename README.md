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

## Run

```bash
python main.py
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
