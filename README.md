# F1-Simulation-

Predicts F1 Driver and Constructor champions using a multi-factor Monte Carlo model.

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

## How It Works

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

- `--simulations`: number of simulated seasons (minimum effective floor: 200)
- `--seed`: random seed for reproducible results
- `--top`: how many top rows to display in each summary table

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
- Current season champion and standings forecast
- Next season projected champion and standings forecast
- Visual probability bars for title outcomes

## Files

- `app.py`: simulation engine and prediction logic
- `main.py`: CLI runner and formatted output
- `web_app.py`: Flask web dashboard entry point
- `templates/index.html`: dashboard page template
- `static/styles.css`: dashboard styling
