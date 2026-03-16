from __future__ import annotations

import argparse

from app import SeasonPrediction, predict_current_and_next_season


def _print_prediction(title: str, prediction: SeasonPrediction, top_n: int) -> None:
	print(f"\n{title}")
	print("=" * len(title))
	print(f"Predicted Driver Champion: {prediction.champion_driver}")
	print(f"Predicted Constructor Champion: {prediction.champion_constructor}\n")

	print("Top Driver Title Probabilities:")
	for idx, (driver, probability) in enumerate(prediction.driver_title_probabilities.items()):
		if idx >= top_n:
			break
		print(f"  {idx + 1:>2}. {driver:<16} {probability * 100:>6.2f}%")

	print("\nTop Constructor Title Probabilities:")
	for idx, (team, probability) in enumerate(prediction.constructor_title_probabilities.items()):
		if idx >= top_n:
			break
		print(f"  {idx + 1:>2}. {team:<16} {probability * 100:>6.2f}%")

	print("\nExpected Driver Standings:")
	for idx, (driver, points) in enumerate(prediction.expected_driver_points.items()):
		if idx >= top_n:
			break
		print(f"  {idx + 1:>2}. {driver:<16} {points:>7.1f} pts")

	print("\nExpected Constructor Standings:")
	for idx, (team, points) in enumerate(prediction.expected_constructor_points.items()):
		if idx >= top_n:
			break
		print(f"  {idx + 1:>2}. {team:<16} {points:>7.1f} pts")


def main() -> None:
	parser = argparse.ArgumentParser(
		description="Predict F1 driver and constructor champions with multi-factor simulation."
	)
	parser.add_argument(
		"--simulations",
		type=int,
		default=3000,
		help="Number of Monte Carlo season simulations (default: 3000)",
	)
	parser.add_argument(
		"--seed",
		type=int,
		default=42,
		help="Random seed for reproducible predictions (default: 42)",
	)
	parser.add_argument(
		"--top",
		type=int,
		default=5,
		help="How many top rows to display per table (default: 5)",
	)

	args = parser.parse_args()

	current_prediction, next_prediction = predict_current_and_next_season(
		simulations=max(200, args.simulations),
		seed=args.seed,
	)

	print("F1 Championship Predictor")
	print("Model factors: engine, aero, chassis, grip, reliability, strategy, pit stop, weather, incidents, and development trend.")

	_print_prediction("Current Season Forecast", current_prediction, top_n=max(1, args.top))
	_print_prediction("Next Season Forecast", next_prediction, top_n=max(1, args.top))


if __name__ == "__main__":
	main()
