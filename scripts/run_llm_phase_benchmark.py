"""Executa uma fase do bolao das LLMs direto pelo terminal."""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from contextlib import suppress
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from copamind.core.config import get_settings
from copamind.data.fifa_stats import team_label
from copamind.data.repositories import DuckDBRepository
from copamind.data.schemas import Match, MatchStatus, PoolPrediction, PoolResult
from copamind.llm.client import LLMError, LMStudioClient
from copamind.pool.llm_agent import (
    BolaoLLMAgent,
    LLMMatchPick,
    LLMModelConsensus,
    LLMRunResult,
    build_combo_pick,
    build_model_consensus_from_runs,
    classify_local_model,
)
from copamind.pool.llm_progress import write_llm_phase_progress
from copamind.pool.scoring import bolao_points, brier_score, outcome


def main() -> None:
    args = _parse_args()
    client = LMStudioClient(timeout=args.timeout)
    with DuckDBRepository(get_settings().duckdb_path) as repo:
        repo.create_schema()
        matches = _phase_matches(
            repo,
            args.phase,
            finished_only=args.finished_only,
            model_id=args.model[0] if len(args.model) == 1 else None,
        )
        if not matches:
            _write_failed_progress(args.batch_id, args.phase, "Nenhum jogo encontrado para a fase.")
            raise SystemExit(f"Nenhum jogo encontrado para phase={args.phase}.")
        models = _selected_models(client, include_heavy=args.include_heavy, only=args.model)
        if args.limit:
            models = models[: args.limit]
        if not models:
            _write_failed_progress(args.batch_id, args.phase, "Nenhum modelo participante encontrado no LM Studio.")
            raise SystemExit("Nenhum modelo participante encontrado no LM Studio.")
        remaining = _remaining_match_models(repo, matches, models)
        pending_models = _pending_models(models, remaining)
        if args.dry_run:
            total_calls = sum(len(model_ids) for _match, model_ids in remaining) * args.samples
            print(
                f"DRY RUN phase={args.phase} matches={len(matches)} "
                f"remaining_matches={len(remaining)} models={len(pending_models)} calls={total_calls} mode=model_first"
            )
            for model_id in pending_models:
                model_matches = [match for match, model_ids in remaining if model_id in model_ids]
                print(f"- {model_id}: {len(model_matches)} jogos")
                for match in model_matches:
                    print(f"  - {match.match_id}: {match.home_team_id} x {match.away_team_id}")
            return
        if not remaining:
            batch_id = args.batch_id or _new_id("llmbatch")
            _update_progress(
                {
                    "batch_id": batch_id,
                    "phase": args.phase,
                    "started_monotonic": time.monotonic(),
                    "started_at": datetime.now(UTC).isoformat(),
                    "completed_calls": 0,
                    "total_calls": 0,
                    "total_matches": 0,
                    "total_models": 0,
                    "total_samples": args.samples,
                },
                status="completed",
                message="Nada a retomar: todas as chamadas da fase ja estavam salvas.",
            )
            print("Nada a retomar: todas as chamadas da fase ja estavam salvas.", flush=True)
            if args.export_portal:
                _export_portal()
            return

        batch_id = args.batch_id or _new_id("llmbatch")
        progress = {
            "batch_id": batch_id,
            "phase": args.phase,
            "started_monotonic": time.monotonic(),
            "started_at": datetime.now(UTC).isoformat(),
            "completed_calls": 0,
            "total_calls": sum(len(model_ids) for _match, model_ids in remaining) * args.samples,
            "total_matches": len(remaining),
            "total_models": len(pending_models),
            "total_samples": args.samples,
        }
        _update_progress(
            progress,
            status="running",
            message="Runner model-first iniciado. Preparando primeiro modelo.",
            current_match_index=0,
            current_model_index=0,
            current_sample_index=0,
        )
        print(
            f"Batch {batch_id} | fase={args.phase} | jogos_restantes={len(remaining)} | "
            f"modelos_restantes={len(pending_models)} | chamadas_restantes={progress['total_calls']} | "
            f"samples={args.samples} | mode=model_first",
            flush=True,
        )
        repo.insert_llm_phase_batch(
            batch_id,
            args.phase,
            datetime.now(UTC),
            "running",
            len(remaining),
            pending_models,
        )
        rounds_by_match = _create_match_rounds(repo, remaining, batch_id, args.phase, args.samples)
        match_indexes = {match.match_id: index for index, (match, _models) in enumerate(remaining, 1)}
        failures = 0
        try:
            for model_index, (model_id, model_matches) in enumerate(_model_first_groups(pending_models, remaining), 1):
                print(f"\n[{model_index}/{len(pending_models)}] {model_id} | {len(model_matches)} jogos", flush=True)
                try:
                    for match in model_matches:
                        match_index = match_indexes[match.match_id]
                        print(
                            f"  [{match_index}/{len(remaining)}] {match.match_id} "
                            f"{match.home_team_id} x {match.away_team_id}",
                            end="",
                            flush=True,
                        )
                        _record_result_if_finished(repo, match)
                        try:
                            _run_model_match(
                                repo,
                                client,
                                match,
                                model_id,
                                round_id=rounds_by_match[match.match_id],
                                samples=args.samples,
                                model_index=model_index,
                                total_models=len(pending_models),
                                match_index=match_index,
                                total_matches=len(remaining),
                                progress=progress,
                            )
                        except Exception as exc:  # pragma: no cover - runner resilience
                            failures += 1
                            _update_progress(
                                progress,
                                status="running",
                                message=f"Erro em {model_id} / {match.match_id}: {exc}",
                                current_match_index=match_index,
                                current_match_label=_match_label(match),
                                current_model_index=model_index,
                                current_model_id=model_id,
                            )
                            print(f" -> ERRO {exc}", flush=True)
                finally:
                    with suppress(LLMError):
                        client.unload(model_id)
            _finalize_match_rounds(repo, remaining, rounds_by_match)
            status = "completed" if failures == 0 else "completed_with_errors"
        except KeyboardInterrupt:
            status = "interrupted"
            print("\nInterrompido pelo usuario; progresso salvo.", flush=True)
        repo.update_llm_phase_batch_status(batch_id, status)
        _update_progress(
            progress,
            status=status,
            message=f"Batch finalizado com status={status}.",
            completed_calls=progress["completed_calls"],
        )
        print(f"\nBatch {batch_id} finalizado com status={status}.", flush=True)
        _print_batch_score(repo, batch_id)
    if args.export_portal:
        _export_portal()


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", default="round_of_16")
    parser.add_argument("--batch-id", default="")
    parser.add_argument("--samples", type=int, default=1)
    parser.add_argument("--timeout", type=float, default=300.0)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--model", action="append", default=[])
    parser.add_argument("--exclude-heavy", dest="include_heavy", action="store_false")
    parser.add_argument("--include-heavy", dest="include_heavy", action="store_true")
    parser.add_argument("--include-scheduled", dest="finished_only", action="store_false")
    parser.add_argument("--finished-only", dest="finished_only", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--no-export", dest="export_portal", action="store_false")
    parser.set_defaults(include_heavy=True, finished_only=False, export_portal=True)
    return parser.parse_args()


def _phase_matches(
    repo: DuckDBRepository,
    phase: str,
    *,
    finished_only: bool,
    model_id: str | None = None,
) -> list[Match]:
    matches = [
        match
        for match in repo.list_matches(limit=800)
        if str(match.stage) == phase and str(match.match_id).startswith("fifa:")
    ]
    if finished_only:
        matches = [match for match in matches if str(match.status) == "finished"]
    matches = sorted(matches, key=lambda item: (item.match_date, item.match_id))
    if matches:
        return matches
    if model_id is None:
        return []
    return _projected_phase_matches(repo, phase, model_id)


def _remaining_match_models(
    repo: DuckDBRepository,
    matches: list[Match],
    models: list[str],
) -> list[tuple[Match, list[str]]]:
    """Retorna apenas pares jogo/modelo que ainda nao foram persistidos."""
    completed: set[tuple[str, str]] = set()
    for row in repo.list_llm_model_runs():
        match_id = str(row.get("match_id") or "")
        model_id = str(row.get("model_id") or "")
        if match_id and model_id:
            completed.add((match_id, model_id))
    for prediction in repo.list_pool_predictions():
        model_id = _model_id_from_predictor(prediction.predictor_name)
        if model_id:
            completed.add((str(prediction.match_id), model_id))

    remaining: list[tuple[Match, list[str]]] = []
    for match in matches:
        missing_models = [
            model_id
            for model_id in models
            if (str(match.match_id), str(model_id)) not in completed
        ]
        if missing_models:
            remaining.append((match, missing_models))
    return remaining


def _pending_models(models: list[str], remaining: list[tuple[Match, list[str]]]) -> list[str]:
    """Mantem a ordem do LM Studio, mas so com modelos que ainda tem chamadas."""
    pending = {model_id for _match, model_ids in remaining for model_id in model_ids}
    return [model_id for model_id in models if model_id in pending]


def _model_first_groups(
    models: list[str],
    remaining: list[tuple[Match, list[str]]],
) -> list[tuple[str, list[Match]]]:
    """Agrupa a execucao como modelo -> jogos pendentes."""
    groups: list[tuple[str, list[Match]]] = []
    for model_id in models:
        model_matches = [match for match, model_ids in remaining if model_id in model_ids]
        if model_matches:
            groups.append((model_id, model_matches))
    return groups


def _projected_phase_matches(repo: DuckDBRepository, phase: str, model_id: str) -> list[Match]:
    if phase == "semifinal":
        teams = [_winner_from_match(repo, match, model_id) for match in _official_phase_matches(repo, "quarterfinal")]
        return _pair_projected_matches(phase, model_id, [team for team in teams if team])
    if phase == "third_place":
        semifinals = _official_phase_matches(repo, "semifinal") or _projected_phase_matches(
            repo, "semifinal", model_id
        )
        teams = [_loser_from_match(repo, match, model_id) for match in semifinals]
        return _pair_projected_matches(phase, model_id, [team for team in teams if team])
    if phase == "final":
        semifinals = _official_phase_matches(repo, "semifinal") or _projected_phase_matches(
            repo, "semifinal", model_id
        )
        teams = [_winner_from_match(repo, match, model_id) for match in semifinals]
        return _pair_projected_matches(phase, model_id, [team for team in teams if team])
    return []


def _official_phase_matches(repo: DuckDBRepository, phase: str) -> list[Match]:
    return sorted(
        [
            match
            for match in repo.list_matches(limit=800)
            if str(match.stage) == phase and str(match.match_id).startswith("fifa:")
        ],
        key=lambda item: (item.match_date, item.match_id),
    )


def _pair_projected_matches(phase: str, model_id: str, team_ids: list[str]) -> list[Match]:
    rows: list[Match] = []
    now = datetime.now(UTC)
    for index in range(0, len(team_ids) - 1, 2):
        rows.append(
            Match(
                match_id=f"projected:{phase}:{_safe_model_id(model_id)}:{index // 2}",
                competition="FIFA World Cup 2026",
                stage=phase,
                match_date=now,
                home_team_id=team_ids[index],
                away_team_id=team_ids[index + 1],
                neutral_venue=True,
                status=MatchStatus.scheduled,
                importance_weight=1.0,
                source="copamind-projection",
                collected_at=now,
                available_at=now,
                snapshot_id="copamind-projection",
            )
        )
    return rows


def _winner_from_match(repo: DuckDBRepository, match: Match, model_id: str) -> str | None:
    side = _actual_winner_side(match) or _predicted_winner_side(repo, match.match_id, model_id)
    if side == "home":
        return match.home_team_id
    if side == "away":
        return match.away_team_id
    return _stronger_team(match.home_team_id, match.away_team_id)


def _loser_from_match(repo: DuckDBRepository, match: Match, model_id: str) -> str | None:
    winner = _winner_from_match(repo, match, model_id)
    if winner == match.home_team_id:
        return match.away_team_id
    if winner == match.away_team_id:
        return match.home_team_id
    return None


def _actual_winner_side(match: Match) -> str | None:
    if match.home_score is None or match.away_score is None:
        return None
    if match.home_score > match.away_score:
        return "home"
    if match.away_score > match.home_score:
        return "away"
    return None


def _predicted_winner_side(repo: DuckDBRepository, match_id: str, model_id: str) -> str | None:
    predictions = [
        prediction
        for prediction in repo.list_pool_predictions()
        if prediction.match_id == match_id and _model_id_from_predictor(prediction.predictor_name) == model_id
    ]
    if not predictions:
        return None
    prediction = max(predictions, key=lambda item: item.locked_at)
    payloads = {
        item["prediction_id"]: item["payload"]
        for item in repo.list_pool_prediction_payloads()
        if item["prediction_id"] == prediction.prediction_id
    }
    payload = payloads.get(prediction.prediction_id, {})
    pick = payload.get("pick") if isinstance(payload, dict) else None
    if isinstance(pick, dict) and pick.get("goes_to_penalties") and pick.get("penalty_winner") in {
        "home",
        "away",
    }:
        return str(pick["penalty_winner"])
    if prediction.predicted_home_goals > prediction.predicted_away_goals:
        return "home"
    if prediction.predicted_away_goals > prediction.predicted_home_goals:
        return "away"
    return "home" if prediction.prob_home >= prediction.prob_away else "away"


def _stronger_team(home_team_id: str, away_team_id: str) -> str:
    # Tie-break deterministico quando ainda nao ha palpite do proprio modelo.
    return min(home_team_id, away_team_id)


def _model_id_from_predictor(predictor_name: str) -> str:
    value = str(predictor_name)
    if value.startswith("llm:") and ":round:" in value:
        return value.removeprefix("llm:").split(":round:", 1)[0]
    return value


def _safe_model_id(model_id: str) -> str:
    return "".join(char if char.isalnum() else "-" for char in model_id).strip("-")[:80] or "model"


def _match_label(match: Match) -> str:
    return f"{team_label(match.home_team_id)} x {team_label(match.away_team_id)}"


def _write_failed_progress(batch_id: str, phase: str, message: str) -> None:
    if not batch_id:
        return
    write_llm_phase_progress(
        batch_id,
        phase=phase,
        status="failed",
        message=message,
        percent=0.0,
        completed_calls=0,
        total_calls=0,
        elapsed_seconds=0.0,
        eta_seconds=None,
    )


def _update_progress(progress: dict[str, object], **fields: object) -> None:
    progress.update(fields)
    total_calls = int(progress.get("total_calls") or 0)
    completed_calls = int(progress.get("completed_calls") or 0)
    started_monotonic = float(progress.get("started_monotonic") or time.monotonic())
    elapsed = max(0.0, time.monotonic() - started_monotonic)
    eta = None
    if completed_calls and total_calls and completed_calls < total_calls:
        eta = (elapsed / completed_calls) * (total_calls - completed_calls)
    percent = (completed_calls / total_calls * 100) if total_calls else float(progress.get("percent") or 0)
    write_llm_phase_progress(
        str(progress["batch_id"]),
        phase=str(progress.get("phase") or ""),
        status=str(progress.get("status") or "running"),
        current_match_index=int(progress.get("current_match_index") or 0),
        total_matches=int(progress.get("total_matches") or 0),
        current_match_label=progress.get("current_match_label"),
        current_model_index=int(progress.get("current_model_index") or 0),
        total_models=int(progress.get("total_models") or 0),
        current_model_id=progress.get("current_model_id"),
        current_sample_index=int(progress.get("current_sample_index") or 0),
        total_samples=int(progress.get("total_samples") or 0),
        completed_calls=completed_calls,
        total_calls=total_calls,
        percent=round(percent, 1),
        elapsed_seconds=round(elapsed, 1),
        eta_seconds=round(eta, 1) if eta is not None else None,
        message=progress.get("message"),
        started_at=progress.get("started_at"),
    )


def _selected_models(
    client: LMStudioClient,
    *,
    include_heavy: bool,
    only: list[str],
) -> list[str]:
    model_ids = client.list_models()
    selected: list[str] = []
    only_set = set(only)
    for model_id in model_ids:
        info = classify_local_model(model_id)
        if only_set and model_id not in only_set:
            continue
        if not info.participates:
            continue
        if info.model_class == "heavy" and not include_heavy:
            continue
        selected.append(model_id)
    return selected


def _create_match_rounds(
    repo: DuckDBRepository,
    remaining: list[tuple[Match, list[str]]],
    batch_id: str,
    phase: str,
    samples: int,
) -> dict[str, str]:
    rounds_by_match: dict[str, str] = {}
    for match, model_ids in remaining:
        round_id = _new_id("llmround")
        repo.insert_llm_pool_round(
            round_id,
            match.match_id,
            datetime.now(UTC),
            "running",
            samples,
            model_ids,
            batch_id=batch_id,
            phase=phase,
        )
        rounds_by_match[match.match_id] = round_id
    return rounds_by_match


def _run_model_match(
    repo: DuckDBRepository,
    client: LMStudioClient,
    match: Match,
    model_id: str,
    *,
    round_id: str,
    samples: int,
    model_index: int,
    total_models: int,
    match_index: int,
    total_matches: int,
    progress: dict[str, object],
) -> None:
    agent = BolaoLLMAgent(client, model_id, temperature=0.2)
    runs: list[LLMRunResult] = []
    valid_picks: list[LLMMatchPick] = []
    for sample_index in range(1, samples + 1):
        _update_progress(
            progress,
            status="running",
            message=f"Executando {model_id} em {_match_label(match)}.",
            current_match_index=match_index,
            total_matches=total_matches,
            current_match_label=_match_label(match),
            current_model_index=model_index,
            total_models=total_models,
            current_model_id=model_id,
            current_sample_index=sample_index,
            total_samples=samples,
        )
        result = agent.run(
            repo,
            match,
            sample_index=sample_index,
            previous_picks=valid_picks,
        )
        runs.append(result)
        if result.pick is not None:
            valid_picks.append(result.pick)
        _save_llm_run(repo, match, round_id, result, sample_index)
        progress["completed_calls"] = int(progress["completed_calls"]) + 1
        _update_progress(
            progress,
            status="running",
            message=f"Chamada {sample_index}/{samples} concluida para {model_id}.",
            current_match_index=match_index,
            total_matches=total_matches,
            current_match_label=_match_label(match),
            current_model_index=model_index,
            total_models=total_models,
            current_model_id=model_id,
            current_sample_index=sample_index,
            total_samples=samples,
        )
    consensus = build_model_consensus_from_runs(
        match,
        model_id,
        round_id,
        runs,
        total_samples=samples,
    )
    if consensus is None:
        _save_invalid_payload(repo, match, round_id, model_id, runs)
        print(" -> invalido", flush=True)
        return
    _save_consensus(repo, match, consensus)
    _lock_pick(
        repo,
        match,
        consensus.predictor_name,
        consensus.pick,
        _consensus_payload(consensus),
    )
    pick = consensus.pick
    print(
        f" -> {pick.predicted_home_goals}-{pick.predicted_away_goals} "
        f"{pick.winner}",
        flush=True,
    )


def _finalize_match_rounds(
    repo: DuckDBRepository,
    remaining: list[tuple[Match, list[str]]],
    rounds_by_match: dict[str, str],
) -> None:
    for match, _model_ids in remaining:
        round_id = rounds_by_match[match.match_id]
        consensuses = _consensuses_for_round(repo, round_id)
        _save_combo_for_round(repo, match, round_id, consensuses)
        repo.update_llm_pool_round_status(round_id, "completed" if consensuses else "failed")


def _consensuses_for_round(repo: DuckDBRepository, round_id: str) -> list[LLMModelConsensus]:
    consensuses: list[LLMModelConsensus] = []
    for row in repo.list_llm_model_consensus(round_id=round_id):
        payload = row.get("payload") if isinstance(row, dict) else None
        if not isinstance(payload, dict):
            continue
        runs = [LLMRunResult.model_validate(item) for item in payload.get("runs", []) if isinstance(item, dict)]
        pick_data = payload.get("pick")
        if not isinstance(pick_data, dict):
            continue
        consensuses.append(
            LLMModelConsensus(
                round_id=str(row["round_id"]),
                model_id=str(row["model_id"]),
                predictor_name=str(row["predictor_name"]),
                pick=LLMMatchPick.model_validate(pick_data),
                valid_samples=int(row["valid_samples"]),
                total_samples=int(row["total_samples"]),
                coherence_score=float(row["coherence_score"]),
                coherence_notes=str(row.get("coherence_notes") or ""),
                runs=runs,
            )
        )
    return consensuses


def _save_combo_for_round(
    repo: DuckDBRepository,
    match: Match,
    round_id: str,
    consensuses: list[LLMModelConsensus],
) -> None:
    combo = build_combo_pick(match, [item.pick for item in consensuses])
    if combo is not None:
        _lock_pick(
            repo,
            match,
            f"combo:llm_pool:round:{round_id}",
            combo,
            {
                "status": "valid",
                "source": "combo",
                "round_id": round_id,
                "models": [item.model_id for item in consensuses],
                "pick": combo.model_dump(),
            },
        )


def _record_result_if_finished(repo: DuckDBRepository, match: Match) -> None:
    if str(match.status) != "finished" or match.home_score is None or match.away_score is None:
        return
    repo.upsert_pool_result(
        PoolResult(
            match_id=match.match_id,
            home_score=match.home_score,
            away_score=match.away_score,
            recorded_at=datetime.now(UTC),
        )
    )


def _lock_pick(
    repo: DuckDBRepository,
    match: Match,
    predictor_name: str,
    pick: LLMMatchPick,
    payload: dict[str, object],
) -> bool:
    prediction_id = f"{predictor_name}:{match.match_id}"
    locked_at = datetime.now(UTC)
    if repo.pool_prediction_exists(prediction_id):
        repo.upsert_pool_prediction_payload(
            prediction_id,
            predictor_name,
            match.match_id,
            payload | {"locked": False, "reason": "prediction_exists"},
            locked_at,
        )
        return False
    data = pick.as_pool_prediction()
    repo.insert_pool_prediction(
        PoolPrediction(
            prediction_id=prediction_id,
            predictor_name=predictor_name,
            match_id=match.match_id,
            snapshot_id=repo.latest_snapshot_id() or "adhoc",
            home_team_id=match.home_team_id,
            away_team_id=match.away_team_id,
            prob_home=data.prob_home,
            prob_draw=data.prob_draw,
            prob_away=data.prob_away,
            predicted_home_goals=data.predicted_home_goals,
            predicted_away_goals=data.predicted_away_goals,
            locked_at=locked_at,
        )
    )
    repo.upsert_pool_prediction_payload(
        prediction_id,
        predictor_name,
        match.match_id,
        payload | {"locked": True},
        locked_at,
    )
    return True


def _save_llm_run(
    repo: DuckDBRepository,
    match: Match,
    round_id: str,
    result: LLMRunResult,
    sample_index: int,
) -> None:
    repo.insert_llm_model_run(
        run_id=f"{round_id}:{result.model_id}:{sample_index}",
        round_id=round_id,
        match_id=match.match_id,
        model_id=result.model_id,
        predictor_name=result.predictor_name,
        sample_index=sample_index,
        prompt_tokens=result.prompt_tokens,
        completion_tokens=result.completion_tokens,
        latency_ms=result.latency_ms,
        raw_response=result.raw_response,
        valid=result.pick is not None,
        error=result.error,
        attempts=result.attempts,
        pick=result.pick.model_dump() if result.pick else None,
        created_at=datetime.now(UTC),
    )


def _save_consensus(
    repo: DuckDBRepository,
    match: Match,
    consensus: LLMModelConsensus,
) -> None:
    pick = consensus.pick
    repo.upsert_llm_model_consensus(
        consensus_id=f"{consensus.round_id}:{consensus.model_id}",
        round_id=consensus.round_id,
        match_id=match.match_id,
        model_id=consensus.model_id,
        predictor_name=consensus.predictor_name,
        valid_samples=consensus.valid_samples,
        total_samples=consensus.total_samples,
        prob_home=pick.prob_home,
        prob_draw=pick.prob_draw,
        prob_away=pick.prob_away,
        predicted_home_goals=pick.predicted_home_goals,
        predicted_away_goals=pick.predicted_away_goals,
        winner=pick.winner,
        first_goal_scorer=pick.first_goal_scorer,
        coherence_score=consensus.coherence_score,
        coherence_notes=consensus.coherence_notes,
        payload=_consensus_payload(consensus),
        created_at=datetime.now(UTC),
    )


def _save_invalid_payload(
    repo: DuckDBRepository,
    match: Match,
    round_id: str,
    model_id: str,
    runs: list[LLMRunResult],
) -> None:
    prediction_id = f"llm:{model_id}:round:{round_id}:{match.match_id}:invalid"
    repo.upsert_pool_prediction_payload(
        prediction_id,
        f"llm:{model_id}:round:{round_id}",
        match.match_id,
        {
            "status": "invalid",
            "round_id": round_id,
            "model_id": model_id,
            "runs": [run.model_dump() for run in runs],
        },
        datetime.now(UTC),
    )


def _consensus_payload(consensus: LLMModelConsensus) -> dict[str, object]:
    return {
        "status": "valid",
        "round_id": consensus.round_id,
        "model_id": consensus.model_id,
        "valid_samples": consensus.valid_samples,
        "total_samples": consensus.total_samples,
        "coherence_score": consensus.coherence_score,
        "coherence_notes": consensus.coherence_notes,
        "runs": [run.model_dump() for run in consensus.runs],
        "pick": consensus.pick.model_dump(),
    }


def _print_batch_score(repo: DuckDBRepository, batch_id: str) -> None:
    rounds = repo.list_llm_pool_rounds(batch_id=batch_id)
    round_ids = {row["round_id"] for row in rounds}
    results = {result.match_id: result for result in repo.list_pool_results()}
    rows = []
    for prediction in repo.list_pool_predictions():
        if not _prediction_in_rounds(prediction.predictor_name, round_ids):
            continue
        result = results.get(prediction.match_id)
        if result is None:
            continue
        actual = outcome(result.home_score, result.away_score)
        predicted = outcome(prediction.predicted_home_goals, prediction.predicted_away_goals)
        rows.append(
            {
                "predictor": prediction.predictor_name,
                "points": bolao_points(
                    prediction.predicted_home_goals,
                    prediction.predicted_away_goals,
                    result.home_score,
                    result.away_score,
                ),
                "winner_hit": predicted == actual,
                "exact": (
                    prediction.predicted_home_goals == result.home_score
                    and prediction.predicted_away_goals == result.away_score
                ),
                "brier": brier_score(
                    prediction.prob_home,
                    prediction.prob_draw,
                    prediction.prob_away,
                    actual,
                ),
            }
        )
    by_predictor: dict[str, list[dict[str, object]]] = {}
    for row in rows:
        by_predictor.setdefault(str(row["predictor"]), []).append(row)
    table = []
    for predictor, items in by_predictor.items():
        scored = len(items)
        table.append(
            {
                "predictor": predictor,
                "jogos": scored,
                "pontos": sum(int(item["points"]) for item in items),
                "vencedor": sum(1 for item in items if item["winner_hit"]),
                "exato": sum(1 for item in items if item["exact"]),
                "brier": sum(float(item["brier"]) for item in items) / scored if scored else 0,
            }
        )
    table.sort(key=lambda item: (item["pontos"], item["vencedor"], -item["brier"]), reverse=True)
    print("\nScore do batch:")
    for item in table[:20]:
        print(
            f"{item['pontos']:>3} pts | {item['vencedor']}/{item['jogos']} vencedor | "
            f"{item['exato']} exatos | brier {item['brier']:.3f} | {item['predictor']}"
        )


def _prediction_in_rounds(predictor_name: str, round_ids: set[str]) -> bool:
    return any(f":round:{round_id}" in predictor_name for round_id in round_ids)


def _export_portal() -> None:
    script = Path("scripts/export_portal_data.py")
    subprocess.run([sys.executable, str(script)], check=False)


def _new_id(prefix: str) -> str:
    return f"{prefix}-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}-{uuid4().hex[:8]}"


if __name__ == "__main__":
    main()
