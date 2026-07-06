"""Simulador Monte Carlo do torneio (MASTER_PLAN §19).

Independente dos LLMs. Determinístico por ``seed``. As probabilidades de cada
confronto vêm do modelo Poisson (E4). O motor simula fase de grupos (turno único)
e mata-mata de eliminação simples, com desempate por saldo e gols e pênaltis em
caso de empate no mata-mata.
"""

from __future__ import annotations

from itertools import combinations

import numpy as np
from pydantic import BaseModel, Field, model_validator

from copamind.models.poisson import PoissonModel

_STAGE_NAMES = {
    2: ["final"],
    4: ["semifinal", "final"],
    8: ["quarterfinal", "semifinal", "final"],
    16: ["round_of_16", "quarterfinal", "semifinal", "final"],
    32: ["round_of_32", "round_of_16", "quarterfinal", "semifinal", "final"],
}


def _is_power_of_two(value: int) -> bool:
    return value >= 2 and (value & (value - 1)) == 0


class TournamentConfig(BaseModel):
    """Configuração do torneio a simular."""

    groups: dict[str, list[str]] = Field(min_length=1)
    advance_per_group: int = Field(default=2, ge=1)
    iterations: int = Field(default=10_000, ge=1)
    seed: int = 2026

    @model_validator(mode="after")
    def _validate(self) -> TournamentConfig:
        for name, teams in self.groups.items():
            if len(teams) < self.advance_per_group:
                raise ValueError(f"grupo {name} tem menos times que advance_per_group")
            if len(set(teams)) != len(teams):
                raise ValueError(f"grupo {name} contém times duplicados")
        qualifiers = len(self.groups) * self.advance_per_group
        if not _is_power_of_two(qualifiers):
            raise ValueError(f"número de classificados ({qualifiers}) deve ser potência de 2")
        return self

    @property
    def qualifiers_count(self) -> int:
        """Total de seleções que avançam ao mata-mata."""
        return len(self.groups) * self.advance_per_group


class TeamResult(BaseModel):
    """Probabilidades simuladas de uma seleção."""

    team_id: str
    qualified_probability: float = Field(ge=0, le=1)
    champion_probability: float = Field(ge=0, le=1)
    stage_probabilities: dict[str, float]


class SimulationResult(BaseModel):
    """Resultado agregado da simulação."""

    iterations: int
    seed: int
    teams: list[TeamResult]


class MonteCarloSimulator:
    """Executa a simulação Monte Carlo do torneio."""

    def __init__(self, model: PoissonModel, config: TournamentConfig) -> None:
        self._model = model
        self._config = config
        self._stats: dict[tuple[str, str], tuple[float, float, float]] = {}

    def _pair_stats(self, home: str, away: str) -> tuple[float, float, float]:
        """Retorna (lambda_home, lambda_away, prob_home_no_draw) em campo neutro."""
        key = (home, away)
        cached = self._stats.get(key)
        if cached is not None:
            return cached
        lam_home, lam_away = self._model.expected_goals(home, away, neutral_venue=True)
        prediction = self._model.predict_match(home, away, neutral_venue=True)
        denom = prediction.prob_home_win + prediction.prob_away_win
        p_home_no_draw = prediction.prob_home_win / denom if denom > 0 else 0.5
        result = (lam_home, lam_away, p_home_no_draw)
        self._stats[key] = result
        return result

    def _play_knockout(self, home: str, away: str, rng: np.random.Generator) -> str:
        lam_home, lam_away, p_home_no_draw = self._pair_stats(home, away)
        home_goals = int(rng.poisson(lam_home))
        away_goals = int(rng.poisson(lam_away))
        if home_goals > away_goals:
            return home
        if away_goals > home_goals:
            return away
        return home if rng.random() < p_home_no_draw else away

    def simulate(self) -> SimulationResult:
        """Roda todas as iterações e agrega as probabilidades."""
        config = self._config
        rng = np.random.default_rng(config.seed)
        n = config.iterations
        all_teams = [team for teams in config.groups.values() for team in teams]

        stage_names = _STAGE_NAMES[config.qualifiers_count]
        qualified = dict.fromkeys(all_teams, 0)
        champion = dict.fromkeys(all_teams, 0)
        reached: dict[str, dict[str, int]] = {
            team: dict.fromkeys(stage_names, 0) for team in all_teams
        }

        group_goals = self._presample_group_goals(rng, n)

        for s in range(n):
            qualifiers = self._simulate_groups(config, group_goals, s, qualified)
            current = qualifiers
            for stage in stage_names:
                winners: list[str] = []
                for i in range(0, len(current), 2):
                    home, away = current[i], current[i + 1]
                    reached[home][stage] += 1
                    reached[away][stage] += 1
                    winners.append(self._play_knockout(home, away, rng))
                current = winners
            champion[current[0]] += 1

        teams = [
            TeamResult(
                team_id=team,
                qualified_probability=qualified[team] / n,
                champion_probability=champion[team] / n,
                stage_probabilities={stage: reached[team][stage] / n for stage in stage_names},
            )
            for team in all_teams
        ]
        teams.sort(key=lambda t: t.champion_probability, reverse=True)
        return SimulationResult(iterations=n, seed=config.seed, teams=teams)

    def _presample_group_goals(
        self, rng: np.random.Generator, n: int
    ) -> dict[str, list[tuple[str, str, np.ndarray, np.ndarray]]]:
        """Pré-amostra os gols de cada partida de grupo para todas as iterações."""
        group_goals: dict[str, list[tuple[str, str, np.ndarray, np.ndarray]]] = {}
        for name, teams in self._config.groups.items():
            matches: list[tuple[str, str, np.ndarray, np.ndarray]] = []
            for home, away in combinations(teams, 2):
                lam_home, lam_away, _ = self._pair_stats(home, away)
                home_goals = rng.poisson(lam_home, size=n)
                away_goals = rng.poisson(lam_away, size=n)
                matches.append((home, away, home_goals, away_goals))
            group_goals[name] = matches
        return group_goals

    def _simulate_groups(
        self,
        config: TournamentConfig,
        group_goals: dict[str, list[tuple[str, str, np.ndarray, np.ndarray]]],
        s: int,
        qualified: dict[str, int],
    ) -> list[str]:
        """Simula a fase de grupos da iteração ``s`` e retorna os classificados."""
        ranked_by_group: list[list[str]] = []
        for name, teams in config.groups.items():
            points = dict.fromkeys(teams, 0)
            goal_diff = dict.fromkeys(teams, 0)
            goals_for = dict.fromkeys(teams, 0)
            for home, away, home_goals, away_goals in group_goals[name]:
                hg = int(home_goals[s])
                ag = int(away_goals[s])
                goals_for[home] += hg
                goals_for[away] += ag
                goal_diff[home] += hg - ag
                goal_diff[away] += ag - hg
                if hg > ag:
                    points[home] += 3
                elif ag > hg:
                    points[away] += 3
                else:
                    points[home] += 1
                    points[away] += 1
            ranked = sorted(
                teams,
                key=lambda t: (points[t], goal_diff[t], goals_for[t]),
                reverse=True,
            )
            ranked_by_group.append(ranked)
            for team in ranked[: config.advance_per_group]:
                qualified[team] += 1

        qualifiers: list[str] = []
        for position in range(config.advance_per_group):
            for ranked in ranked_by_group:
                qualifiers.append(ranked[position])
        return qualifiers
