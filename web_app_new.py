from __future__ import annotations

import os
from typing import Dict, List, Tuple

from flask import Flask, render_template, request

from app import SeasonPrediction, predict_current_and_next_season


# Get the directory where this script is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, 'templates'),
    static_folder=os.path.join(BASE_DIR, 'static'),
    static_url_path='/static'
)


def _top_items(mapping: Dict[str, float], top_n: int) -> List[Tuple[int, str, float]]:
    rows: List[Tuple[int, str, float]] = []
    for idx, (name, value) in enumerate(mapping.items(), start=1):
        if idx > top_n:
            break
        rows.append((idx, name, value))
    return rows


def _prediction_view_model(prediction: SeasonPrediction, top_n: int) -> Dict[str, object]:
    return {
        "champion_driver": prediction.champion_driver,
        "champion_constructor": prediction.champion_constructor,
        "driver_probabilities": [
            (rank, name, probability * 100.0)
            for rank, name, probability in _top_items(prediction.driver_title_probabilities, top_n)
        ],
        "constructor_probabilities": [
            (rank, name, probability * 100.0)
            for rank, name, probability in _top_items(prediction.constructor_title_probabilities, top_n)
        ],
        "driver_points": _top_items(prediction.expected_driver_points, top_n),
        "constructor_points": _top_items(prediction.expected_constructor_points, top_n),
    }


@app.route("/")
def landing() -> str:
    """Serve the F1 SIM landing page"""
    return render_template("landing.html")


@app.route("/simulation", methods=["GET", "POST"])
def simulation() -> str:
    simulations = 3000
    seed = 42
    top = 8
    year: int | None = None
    qualifying_weight = 0.28
    safety_car_rate = 0.26
    tire_impact = 0.32
    reliability_sensitivity = 0.30
    chaos_level = 0.35

    if request.method == "POST":
        simulations = max(200, int(request.form.get("simulations", simulations)))
        seed = int(request.form.get("seed", seed))
        top = max(3, min(20, int(request.form.get("top", top))))
        year_raw = request.form.get("year", "").strip()
        year = int(year_raw) if year_raw else None
        qualifying_weight = max(0.0, min(1.0, float(request.form.get("qualifying_weight", qualifying_weight))))
        safety_car_rate = max(0.0, min(1.0, float(request.form.get("safety_car_rate", safety_car_rate))))
        tire_impact = max(0.0, min(1.0, float(request.form.get("tire_impact", tire_impact))))
        reliability_sensitivity = max(0.0, min(1.0, float(request.form.get("reliability_sensitivity", reliability_sensitivity))))
        chaos_level = max(0.0, min(1.0, float(request.form.get("chaos_level", chaos_level))))

    current_prediction, next_prediction = predict_current_and_next_season(
        simulations=simulations,
        seed=seed,
        season_year=year,
        qualifying_weight=qualifying_weight,
        safety_car_rate=safety_car_rate,
        tire_degradation_impact=tire_impact,
        reliability_sensitivity=reliability_sensitivity,
        chaos_level=chaos_level,
    )

    return render_template(
        "index.html",
        simulations=simulations,
        seed=seed,
        top=top,
        year="" if year is None else year,
        qualifying_weight=qualifying_weight,
        safety_car_rate=safety_car_rate,
        tire_impact=tire_impact,
        reliability_sensitivity=reliability_sensitivity,
        chaos_level=chaos_level,
        current=_prediction_view_model(current_prediction, top),
        next_season=_prediction_view_model(next_prediction, top),
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
