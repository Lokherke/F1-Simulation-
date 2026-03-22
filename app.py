from __future__ import annotations

from datetime import datetime, timezone
from dataclasses import dataclass
import hashlib
from pathlib import Path
from typing import Dict, List, Tuple
import random


POINTS_TABLE = [25, 18, 15, 12, 10, 8, 6, 4, 2, 1]
FASTF1_CACHE_DIR = Path(__file__).resolve().parent / ".fastf1_cache"


@dataclass(frozen=True)
class Team:
	name: str
	engine_performance: float
	aero_efficiency: float
	chassis_balance: float
	mechanical_grip: float
	reliability: float
	pit_stop_efficiency: float
	strategy_quality: float
	tire_management: float
	development_rate: float
	regulation_adaptability: float


@dataclass(frozen=True)
class Driver:
	name: str
	team: str
	pace: float
	consistency: float
	racecraft: float
	wet_skill: float
	tire_feedback: float
	adaptability: float


@dataclass(frozen=True)
class TrackProfile:
	name: str
	power_sensitivity: float
	aero_sensitivity: float
	grip_sensitivity: float
	overtaking_difficulty: float
	weather_volatility: float


@dataclass(frozen=True)
class SeasonPrediction:
	champion_driver: str
	champion_constructor: str
	driver_title_probabilities: Dict[str, float]
	constructor_title_probabilities: Dict[str, float]
	expected_driver_points: Dict[str, float]
	expected_constructor_points: Dict[str, float]


@dataclass(frozen=True)
class SimulationConfig:
	qualifying_weight: float = 0.28
	safety_car_rate: float = 0.26
	tire_degradation_impact: float = 0.32
	reliability_sensitivity: float = 0.30
	chaos_level: float = 0.35


def _sanitize_config(config: SimulationConfig | None) -> SimulationConfig:
	if config is None:
		return SimulationConfig()
	return SimulationConfig(
		qualifying_weight=_clamp(config.qualifying_weight, 0.0, 1.0),
		safety_car_rate=_clamp(config.safety_car_rate, 0.0, 1.0),
		tire_degradation_impact=_clamp(config.tire_degradation_impact, 0.0, 1.0),
		reliability_sensitivity=_clamp(config.reliability_sensitivity, 0.0, 1.0),
		chaos_level=_clamp(config.chaos_level, 0.0, 1.0),
	)


def _clamp(value: float, minimum: float = 0.0, maximum: float = 100.0) -> float:
	return max(minimum, min(maximum, value))


def _stable_uniform(key: str, minimum: float, maximum: float) -> float:
	digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
	ratio = int(digest[:16], 16) / float(16**16 - 1)
	return minimum + (maximum - minimum) * ratio


def _safe_float(value: object, default: float = 0.0) -> float:
	try:
		parsed = float(value)
		if parsed != parsed:
			return default
		return parsed
	except (TypeError, ValueError):
		return default


def _safe_int(value: object, default: int = 20) -> int:
	try:
		parsed = int(float(value))
		if parsed <= 0:
			return default
		return parsed
	except (TypeError, ValueError):
		return default


def _normalize(values: Dict[str, float]) -> Dict[str, float]:
	if not values:
		return {}
	minimum = min(values.values())
	maximum = max(values.values())
	spread = maximum - minimum
	if spread <= 1e-9:
		return {name: 0.5 for name in values}
	return {name: (value - minimum) / spread for name, value in values.items()}


def _build_track_profile_from_event(event_name: str, round_number: int) -> TrackProfile:
	key = f"{event_name}-{round_number}"
	return TrackProfile(
		name=event_name,
		power_sensitivity=_stable_uniform(f"{key}-power", 0.44, 0.96),
		aero_sensitivity=_stable_uniform(f"{key}-aero", 0.45, 0.92),
		grip_sensitivity=_stable_uniform(f"{key}-grip", 0.54, 0.89),
		overtaking_difficulty=_stable_uniform(f"{key}-ot", 0.33, 0.94),
		weather_volatility=_stable_uniform(f"{key}-wx", 0.16, 0.52),
	)


def _load_fastf1_grid_and_calendar(season_year: int | None = None) -> Tuple[List[Team], List[Driver], List[TrackProfile], int]:
	import fastf1

	FASTF1_CACHE_DIR.mkdir(parents=True, exist_ok=True)
	fastf1.Cache.enable_cache(str(FASTF1_CACHE_DIR))

	current_year = datetime.now(timezone.utc).year
	candidate_years = [season_year] if season_year is not None else [current_year, current_year - 1, current_year - 2, current_year - 3]
	today = datetime.now(timezone.utc).date()
	last_error: Exception | None = None

	for year in candidate_years:
		try:
			schedule = fastf1.get_event_schedule(year, include_testing=False)
		except Exception as exc:  # pragma: no cover - external dependency/network failures
			last_error = exc
			continue

		if schedule is None or len(schedule) == 0:
			continue

		calendar: List[TrackProfile] = []
		completed_rounds: List[int] = []
		for _, event in schedule.iterrows():
			round_number = _safe_int(event.get("RoundNumber"), default=0)
			if round_number <= 0:
				continue
			event_name = str(event.get("EventName") or f"Round {round_number}").strip()
			calendar.append(_build_track_profile_from_event(event_name, round_number))

			event_date = event.get("EventDate")
			event_day = event_date.date() if hasattr(event_date, "date") else None
			if event_day is None or event_day <= today:
				completed_rounds.append(round_number)

		if not completed_rounds or not calendar:
			continue

		driver_points: Dict[str, float] = {}
		driver_finish_sum: Dict[str, float] = {}
		driver_finish_count: Dict[str, int] = {}
		driver_team: Dict[str, str] = {}
		team_points: Dict[str, float] = {}
		team_finish_sum: Dict[str, float] = {}
		team_finish_count: Dict[str, int] = {}
		loaded_rounds = 0

		for round_number in completed_rounds:
			try:
				race = fastf1.get_session(year, round_number, "R")
				race.load(laps=False, telemetry=False, weather=False, messages=False)
				results = race.results
			except Exception:  # pragma: no cover - external dependency/network failures
				continue

			if results is None or len(results) == 0:
				continue

			loaded_rounds += 1
			for _, row in results.iterrows():
				driver_name = str(row.get("FullName") or row.get("BroadcastName") or row.get("Abbreviation") or "").strip()
				team_name = str(row.get("TeamName") or "").strip()
				if not driver_name or not team_name:
					continue

				points = _safe_float(row.get("Points"), default=0.0)
				finish_position = _safe_int(row.get("Position"), default=20)

				driver_points[driver_name] = driver_points.get(driver_name, 0.0) + points
				driver_finish_sum[driver_name] = driver_finish_sum.get(driver_name, 0.0) + finish_position
				driver_finish_count[driver_name] = driver_finish_count.get(driver_name, 0) + 1
				driver_team[driver_name] = team_name

				team_points[team_name] = team_points.get(team_name, 0.0) + points
				team_finish_sum[team_name] = team_finish_sum.get(team_name, 0.0) + finish_position
				team_finish_count[team_name] = team_finish_count.get(team_name, 0) + 1

		if loaded_rounds == 0 or not team_points or not driver_points:
			continue

		team_norm_points = _normalize(team_points)
		driver_norm_points = _normalize(driver_points)

		teams: List[Team] = []
		for team_name, points in sorted(team_points.items(), key=lambda entry: entry[1], reverse=True):
			avg_finish = team_finish_sum[team_name] / max(1, team_finish_count[team_name])
			form = 0.70 * team_norm_points[team_name] + 0.30 * _clamp((20.0 - avg_finish) / 19.0, 0.0, 1.0)
			base = _clamp(70.0 + form * 26.0)
			teams.append(
				Team(
					name=team_name,
					engine_performance=_clamp(base + _stable_uniform(f"{team_name}-engine", -4.0, 4.0)),
					aero_efficiency=_clamp(base + _stable_uniform(f"{team_name}-aero", -4.5, 4.5)),
					chassis_balance=_clamp(base + _stable_uniform(f"{team_name}-chassis", -3.5, 4.0)),
					mechanical_grip=_clamp(base + _stable_uniform(f"{team_name}-grip", -3.0, 4.0)),
					reliability=_clamp(base + _stable_uniform(f"{team_name}-rel", -3.5, 5.0)),
					pit_stop_efficiency=_clamp(base + _stable_uniform(f"{team_name}-pit", -4.0, 3.5)),
					strategy_quality=_clamp(base + _stable_uniform(f"{team_name}-strat", -4.0, 3.5)),
					tire_management=_clamp(base + _stable_uniform(f"{team_name}-tire", -3.5, 4.0)),
					development_rate=_clamp(base + _stable_uniform(f"{team_name}-dev", -3.0, 4.0)),
					regulation_adaptability=_clamp(base + _stable_uniform(f"{team_name}-reg", -3.0, 4.0)),
				)
			)

		team_strength = {team.name: (team.engine_performance + team.aero_efficiency + team.chassis_balance) / 3.0 for team in teams}
		drivers: List[Driver] = []
		for driver_name, points in sorted(driver_points.items(), key=lambda entry: entry[1], reverse=True):
			team_name = driver_team.get(driver_name)
			if not team_name:
				continue

			avg_finish = driver_finish_sum[driver_name] / max(1, driver_finish_count[driver_name])
			driver_form = 0.72 * driver_norm_points[driver_name] + 0.28 * _clamp((20.0 - avg_finish) / 19.0, 0.0, 1.0)
			team_factor = _clamp((team_strength.get(team_name, 80.0) - 75.0) / 25.0, 0.0, 1.0)
			base = _clamp(68.0 + driver_form * 24.0 + team_factor * 4.0)
			drivers.append(
				Driver(
					name=driver_name,
					team=team_name,
					pace=_clamp(base + _stable_uniform(f"{driver_name}-pace", -3.5, 4.0)),
					consistency=_clamp(base + _stable_uniform(f"{driver_name}-cons", -3.5, 4.0)),
					racecraft=_clamp(base + _stable_uniform(f"{driver_name}-rc", -3.0, 4.0)),
					wet_skill=_clamp(base + _stable_uniform(f"{driver_name}-wet", -4.5, 4.5)),
					tire_feedback=_clamp(base + _stable_uniform(f"{driver_name}-tire", -3.0, 3.5)),
					adaptability=_clamp(base + _stable_uniform(f"{driver_name}-adp", -3.0, 3.5)),
				)
			)

		if teams and drivers:
			return teams, drivers, calendar, year

	error_message = "Unable to load real F1 data with FastF1."
	if last_error is not None:
		error_message = f"{error_message} Last error: {last_error}"
	raise RuntimeError(error_message)


def build_default_grid() -> Tuple[List[Team], List[Driver]]:
	teams = [
		Team("Red Falcon", 92, 91, 89, 85, 87, 90, 91, 86, 88, 90),
		Team("Silver Arrow", 90, 88, 88, 84, 89, 87, 88, 85, 86, 87),
		Team("Midnight Papaya", 88, 89, 87, 86, 85, 86, 85, 87, 90, 88),
		Team("British Green", 84, 86, 84, 84, 82, 84, 82, 84, 84, 83),
		Team("Alpine Blue", 82, 82, 83, 81, 81, 83, 80, 82, 82, 80),
		Team("Toro Ruby", 81, 80, 80, 79, 80, 82, 79, 80, 81, 80),
		Team("Sauber Lime", 80, 79, 79, 79, 79, 81, 78, 79, 82, 82),
		Team("Atlantic Black", 78, 78, 78, 78, 78, 79, 77, 78, 79, 78),
		Team("Haas Steel", 77, 76, 76, 76, 77, 78, 76, 77, 78, 77),
		Team("Williams Navy", 79, 77, 77, 77, 76, 80, 77, 78, 80, 79),
	]

	drivers = [
		Driver("A. Blaze", "Red Falcon", 95, 91, 92, 88, 89, 92),
		Driver("L. Frost", "Red Falcon", 90, 88, 89, 86, 87, 89),
		Driver("G. Knight", "Silver Arrow", 93, 90, 90, 89, 88, 90),
		Driver("R. Vega", "Silver Arrow", 88, 87, 88, 85, 85, 88),
		Driver("P. Stone", "Midnight Papaya", 91, 89, 90, 87, 88, 90),
		Driver("N. Drake", "Midnight Papaya", 87, 86, 87, 84, 85, 87),
		Driver("F. Hart", "British Green", 86, 85, 86, 83, 84, 85),
		Driver("Y. Cole", "British Green", 84, 83, 84, 81, 82, 84),
		Driver("E. Silva", "Alpine Blue", 84, 82, 84, 82, 83, 83),
		Driver("O. Quinn", "Alpine Blue", 82, 81, 82, 80, 81, 82),
		Driver("D. Rowan", "Toro Ruby", 83, 82, 83, 81, 82, 83),
		Driver("K. Vale", "Toro Ruby", 81, 80, 81, 79, 80, 81),
		Driver("M. Gray", "Sauber Lime", 82, 80, 81, 80, 81, 82),
		Driver("T. Hale", "Sauber Lime", 80, 79, 80, 78, 79, 80),
		Driver("J. Cross", "Atlantic Black", 79, 78, 79, 77, 78, 79),
		Driver("I. Reed", "Atlantic Black", 78, 77, 78, 76, 77, 78),
		Driver("S. Ford", "Haas Steel", 79, 78, 79, 76, 77, 79),
		Driver("B. Lake", "Haas Steel", 77, 76, 77, 75, 76, 77),
		Driver("C. North", "Williams Navy", 80, 79, 80, 78, 79, 81),
		Driver("V. Dale", "Williams Navy", 78, 77, 78, 76, 77, 79),
	]
	return teams, drivers


def build_default_calendar() -> List[TrackProfile]:
	return [
		TrackProfile("Bahrain", 0.72, 0.66, 0.70, 0.48, 0.22),
		TrackProfile("Jeddah", 0.86, 0.62, 0.58, 0.42, 0.18),
		TrackProfile("Melbourne", 0.68, 0.70, 0.66, 0.50, 0.30),
		TrackProfile("Suzuka", 0.65, 0.85, 0.73, 0.60, 0.38),
		TrackProfile("Shanghai", 0.74, 0.72, 0.67, 0.49, 0.27),
		TrackProfile("Miami", 0.78, 0.63, 0.61, 0.44, 0.33),
		TrackProfile("Imola", 0.63, 0.84, 0.76, 0.62, 0.29),
		TrackProfile("Monaco", 0.40, 0.90, 0.88, 0.94, 0.25),
		TrackProfile("Montreal", 0.79, 0.61, 0.65, 0.46, 0.32),
		TrackProfile("Barcelona", 0.64, 0.86, 0.71, 0.58, 0.31),
		TrackProfile("Spielberg", 0.82, 0.62, 0.66, 0.43, 0.40),
		TrackProfile("Silverstone", 0.70, 0.84, 0.69, 0.57, 0.42),
		TrackProfile("Hungaroring", 0.52, 0.88, 0.82, 0.75, 0.30),
		TrackProfile("Spa", 0.83, 0.80, 0.67, 0.48, 0.50),
		TrackProfile("Zandvoort", 0.56, 0.87, 0.79, 0.72, 0.36),
		TrackProfile("Monza", 0.95, 0.46, 0.54, 0.33, 0.24),
		TrackProfile("Baku", 0.89, 0.54, 0.58, 0.40, 0.41),
		TrackProfile("Singapore", 0.48, 0.86, 0.83, 0.78, 0.44),
		TrackProfile("Austin", 0.73, 0.75, 0.72, 0.55, 0.34),
		TrackProfile("Mexico City", 0.76, 0.68, 0.69, 0.52, 0.26),
		TrackProfile("Sao Paulo", 0.70, 0.73, 0.74, 0.56, 0.51),
		TrackProfile("Las Vegas", 0.92, 0.52, 0.57, 0.36, 0.17),
		TrackProfile("Lusail", 0.67, 0.82, 0.71, 0.53, 0.20),
		TrackProfile("Abu Dhabi", 0.74, 0.74, 0.68, 0.50, 0.19),
	]


def _weather_index(track: TrackProfile, rng: random.Random) -> float:
	# 0 means dry race, 1 means very wet and unstable race.
	return _clamp((track.weather_volatility * 100) + rng.gauss(0, 12), 0, 100) / 100


def _performance_score(
	driver: Driver,
	team: Team,
	track: TrackProfile,
	weather_index: float,
	safety_car_factor: float,
	qualifying_advantage: float,
	config: SimulationConfig,
	rng: random.Random,
) -> float:
	# Technical package score by circuit profile.
	car_score = (
		team.engine_performance * track.power_sensitivity * 0.24
		+ team.aero_efficiency * track.aero_sensitivity * 0.24
		+ team.mechanical_grip * track.grip_sensitivity * 0.18
		+ team.chassis_balance * 0.14
		+ team.tire_management * 0.10
		+ team.reliability * 0.10
	)

	# Human/execution score with weather-dependent adjustments.
	driver_score = (
		driver.pace * 0.40
		+ driver.consistency * 0.18
		+ driver.racecraft * (0.16 + 0.08 * track.overtaking_difficulty)
		+ driver.tire_feedback * 0.10
		+ driver.adaptability * 0.08
		+ driver.wet_skill * (0.08 + 0.16 * weather_index)
	)

	# Operations score: strategy and pit stop quality are amplified in volatile conditions.
	operations_score = (
		team.strategy_quality * (0.55 + 0.20 * weather_index)
		+ team.pit_stop_efficiency * (0.45 - 0.05 * weather_index)
	)

	# Tire degradation pressure at high-energy tracks, partially offset by team/driver tire quality.
	tire_wear_pressure = (track.grip_sensitivity * 0.7 + track.aero_sensitivity * 0.3) * (0.45 + weather_index * 0.2)
	tire_wear_resistance = (team.tire_management * 0.65 + driver.tire_feedback * 0.35) / 100
	tire_penalty = config.tire_degradation_impact * max(0.0, tire_wear_pressure - tire_wear_resistance) * 9.0

	# Reliability and incident model.
	dnf_probability = _clamp(
		18 - team.reliability * (0.14 + config.reliability_sensitivity * 0.08) - driver.consistency * 0.07,
		1.5,
		12.0 + config.chaos_level * 4.0,
	) / 100
	if rng.random() < dnf_probability:
		return -200.0

	incident_penalty = 0.0
	incident_threshold = 0.04 + weather_index * 0.06 + config.chaos_level * 0.05 + safety_car_factor * 0.03
	if rng.random() < incident_threshold:
		incident_penalty = rng.uniform(6.0, 16.0 + config.chaos_level * 7.0)

	randomness = rng.gauss(0, 3.2 + weather_index * 2.4 + config.chaos_level * 2.2 + safety_car_factor * 1.4)
	qualifying_bonus = qualifying_advantage * (2.8 + config.qualifying_weight * 7.0)
	safety_car_strategy = (team.strategy_quality - 50.0) / 50.0 * safety_car_factor * 3.0
	return (
		car_score * 0.50
		+ driver_score * 0.34
		+ operations_score * 0.16
		+ randomness
		+ qualifying_bonus
		+ safety_car_strategy
		- incident_penalty
		- tire_penalty
	)


def _simulate_single_race(
	drivers: List[Driver],
	team_map: Dict[str, Team],
	track: TrackProfile,
	config: SimulationConfig,
	rng: random.Random,
) -> List[Tuple[str, str, float]]:
	weather_index = _weather_index(track, rng)
	safety_car_factor = 1.0 if rng.random() < (config.safety_car_rate * (0.45 + track.weather_volatility)) else 0.0

	qualifying_scores: List[Tuple[str, float]] = []
	for driver in drivers:
		team = team_map[driver.team]
		q_score = (
			driver.pace * 0.52
			+ driver.adaptability * 0.12
			+ team.engine_performance * track.power_sensitivity * 0.18
			+ team.aero_efficiency * track.aero_sensitivity * 0.18
			+ rng.gauss(0, 2.1)
		)
		qualifying_scores.append((driver.name, q_score))

	qualifying_scores.sort(key=lambda entry: entry[1], reverse=True)
	grid_advantage_map: Dict[str, float] = {}
	field_size = max(1, len(qualifying_scores) - 1)
	for grid_position, (driver_name, _) in enumerate(qualifying_scores):
		relative = 1.0 - (grid_position / field_size)
		grid_advantage_map[driver_name] = (relative - 0.5) * config.qualifying_weight

	race_scores: List[Tuple[str, str, float]] = []

	for driver in drivers:
		team = team_map[driver.team]
		score = _performance_score(
			driver=driver,
			team=team,
			track=track,
			weather_index=weather_index,
			safety_car_factor=safety_car_factor,
			qualifying_advantage=grid_advantage_map.get(driver.name, 0.0),
			config=config,
			rng=rng,
		)
		race_scores.append((driver.name, driver.team, score))

	race_scores.sort(key=lambda entry: entry[2], reverse=True)
	return race_scores


def _simulate_season_once(
	teams: List[Team],
	drivers: List[Driver],
	calendar: List[TrackProfile],
	config: SimulationConfig,
	rng: random.Random,
) -> Tuple[Dict[str, int], Dict[str, int]]:
	team_map = {team.name: team for team in teams}
	driver_points = {driver.name: 0 for driver in drivers}
	constructor_points = {team.name: 0 for team in teams}

	for track in calendar:
		result = _simulate_single_race(drivers, team_map, track, config, rng)
		for idx, (driver_name, team_name, score) in enumerate(result):
			if idx < len(POINTS_TABLE) and score > -150:
				points = POINTS_TABLE[idx]
				driver_points[driver_name] += points
				constructor_points[team_name] += points

	return driver_points, constructor_points


def _select_champion(points: Dict[str, int], rng: random.Random) -> str:
	top_score = max(points.values())
	tied = [name for name, value in points.items() if value == top_score]
	if len(tied) == 1:
		return tied[0]
	return rng.choice(tied)


def predict_season(
	teams: List[Team],
	drivers: List[Driver],
	calendar: List[TrackProfile],
	simulations: int = 2000,
	seed: int | None = None,
	config: SimulationConfig | None = None,
) -> SeasonPrediction:
	rng = random.Random(seed)
	simulation_config = _sanitize_config(config)
	driver_title_wins = {driver.name: 0 for driver in drivers}
	constructor_title_wins = {team.name: 0 for team in teams}
	total_driver_points = {driver.name: 0 for driver in drivers}
	total_constructor_points = {team.name: 0 for team in teams}

	for _ in range(simulations):
		driver_points, constructor_points = _simulate_season_once(
			teams=teams,
			drivers=drivers,
			calendar=calendar,
			config=simulation_config,
			rng=rng,
		)

		for name, points in driver_points.items():
			total_driver_points[name] += points
		for name, points in constructor_points.items():
			total_constructor_points[name] += points

		driver_champion = _select_champion(driver_points, rng)
		constructor_champion = _select_champion(constructor_points, rng)
		driver_title_wins[driver_champion] += 1
		constructor_title_wins[constructor_champion] += 1

	driver_title_probabilities = {
		name: wins / simulations for name, wins in sorted(driver_title_wins.items(), key=lambda item: item[1], reverse=True)
	}
	constructor_title_probabilities = {
		name: wins / simulations
		for name, wins in sorted(constructor_title_wins.items(), key=lambda item: item[1], reverse=True)
	}
	expected_driver_points = {
		name: total_driver_points[name] / simulations
		for name in sorted(total_driver_points, key=total_driver_points.get, reverse=True)
	}
	expected_constructor_points = {
		name: total_constructor_points[name] / simulations
		for name in sorted(total_constructor_points, key=total_constructor_points.get, reverse=True)
	}

	champion_driver = next(iter(driver_title_probabilities))
	champion_constructor = next(iter(constructor_title_probabilities))

	return SeasonPrediction(
		champion_driver=champion_driver,
		champion_constructor=champion_constructor,
		driver_title_probabilities=driver_title_probabilities,
		constructor_title_probabilities=constructor_title_probabilities,
		expected_driver_points=expected_driver_points,
		expected_constructor_points=expected_constructor_points,
	)


def project_next_season(
	teams: List[Team],
	drivers: List[Driver],
	seed: int | None = None,
) -> Tuple[List[Team], List[Driver]]:
	rng = random.Random(seed)
	projected_teams: List[Team] = []
	projected_drivers: List[Driver] = []

	for team in teams:
		regulation_noise = rng.gauss(0, 2.0)
		technical_gain = (
			team.development_rate * 0.08 + team.regulation_adaptability * 0.06 + regulation_noise
		)

		projected_teams.append(
			Team(
				name=team.name,
				engine_performance=_clamp(team.engine_performance + technical_gain * rng.uniform(0.5, 1.0)),
				aero_efficiency=_clamp(team.aero_efficiency + technical_gain * rng.uniform(0.6, 1.1)),
				chassis_balance=_clamp(team.chassis_balance + technical_gain * rng.uniform(0.5, 1.0)),
				mechanical_grip=_clamp(team.mechanical_grip + technical_gain * rng.uniform(0.5, 1.0)),
				reliability=_clamp(team.reliability + technical_gain * rng.uniform(0.4, 0.9)),
				pit_stop_efficiency=_clamp(team.pit_stop_efficiency + rng.gauss(0.5, 1.4)),
				strategy_quality=_clamp(team.strategy_quality + rng.gauss(0.4, 1.6)),
				tire_management=_clamp(team.tire_management + technical_gain * rng.uniform(0.4, 0.8)),
				development_rate=_clamp(team.development_rate + rng.gauss(0.0, 1.5)),
				regulation_adaptability=_clamp(team.regulation_adaptability + rng.gauss(0.3, 1.8)),
			)
		)

	for driver in drivers:
		trajectory = rng.gauss(0.5, 1.5)
		projected_drivers.append(
			Driver(
				name=driver.name,
				team=driver.team,
				pace=_clamp(driver.pace + trajectory * rng.uniform(0.3, 0.8)),
				consistency=_clamp(driver.consistency + trajectory * rng.uniform(0.2, 0.8)),
				racecraft=_clamp(driver.racecraft + trajectory * rng.uniform(0.2, 0.7)),
				wet_skill=_clamp(driver.wet_skill + trajectory * rng.uniform(0.1, 0.8)),
				tire_feedback=_clamp(driver.tire_feedback + trajectory * rng.uniform(0.2, 0.7)),
				adaptability=_clamp(driver.adaptability + trajectory * rng.uniform(0.3, 0.9)),
			)
		)

	return projected_teams, projected_drivers


def predict_current_and_next_season(
	simulations: int = 2000,
	seed: int | None = None,
	season_year: int | None = None,
	qualifying_weight: float = 0.28,
	safety_car_rate: float = 0.26,
	tire_degradation_impact: float = 0.32,
	reliability_sensitivity: float = 0.30,
	chaos_level: float = 0.35,
) -> Tuple[SeasonPrediction, SeasonPrediction]:
	config = _sanitize_config(
		SimulationConfig(
			qualifying_weight=qualifying_weight,
			safety_car_rate=safety_car_rate,
			tire_degradation_impact=tire_degradation_impact,
			reliability_sensitivity=reliability_sensitivity,
			chaos_level=chaos_level,
		)
	)

	try:
		teams, drivers, calendar, _ = _load_fastf1_grid_and_calendar(season_year=season_year)
	except Exception:
		teams, drivers = build_default_grid()
		calendar = build_default_calendar()

	current_prediction = predict_season(
		teams=teams,
		drivers=drivers,
		calendar=calendar,
		simulations=simulations,
		seed=seed,
		config=config,
	)

	projected_teams, projected_drivers = project_next_season(teams, drivers, seed=None if seed is None else seed + 1)
	next_prediction = predict_season(
		teams=projected_teams,
		drivers=projected_drivers,
		calendar=calendar,
		simulations=simulations,
		seed=None if seed is None else seed + 2,
		config=config,
	)

	return current_prediction, next_prediction
