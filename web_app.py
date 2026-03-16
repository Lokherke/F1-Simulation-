from __future__ import annotations

from typing import Dict, List, Tuple

from flask import Flask, render_template, request

from app import SeasonPrediction, predict_current_and_next_season


app = Flask(__name__)


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


@app.route("/", methods=["GET", "POST"])
def index() -> str:
    simulations = 3000
    seed = 42
    top = 8

    if request.method == "POST":
        simulations = max(200, int(request.form.get("simulations", simulations)))
        seed = int(request.form.get("seed", seed))
        top = max(3, min(20, int(request.form.get("top", top))))

    current_prediction, next_prediction = predict_current_and_next_season(
        simulations=simulations,
        seed=seed,
    )

    return render_template(
        "index.html",
        simulations=simulations,
        seed=seed,
        top=top,
        current=_prediction_view_model(current_prediction, top),
        next_season=_prediction_view_model(next_prediction, top),
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
