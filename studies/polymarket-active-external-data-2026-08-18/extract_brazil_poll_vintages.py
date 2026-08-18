# ruff: noqa: D103, EM101, INP001, S603, S607, T201, TRY003

"""Extract first-public, TSE-matched Lula/Flávio runoff poll vintages from Git history."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import unicodedata
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

_EXPECTED_REMOTE = (
    "https://huggingface.co/datasets/AFOS-Analytics1/brazil-2026-electoral-divergence"
)
_POLL_PATHSPEC = ":(glob)polls/polls-data-*.json"
_REGISTER_PATTERN = re.compile(r"^BR-\d{5}/2026$")


def _git(repo: Path, *arguments: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *arguments],
        check=True,
        capture_output=True,
        text=True,
    ).stdout


def _canonical(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    return "".join(
        character for character in normalized if not unicodedata.combining(character)
    ).lower()


def _protocol_key(value: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", value.upper())


def _runoff_value(poll: dict[str, object]) -> tuple[float, float] | None:
    matches: set[tuple[float, float]] = set()
    for matchup in poll.get("secondRound") or []:
        if not isinstance(matchup, dict):
            continue
        candidate1 = _canonical(str(matchup.get("candidate1", "")))
        candidate2 = _canonical(str(matchup.get("candidate2", "")))
        matchup_names = f"{candidate1} {candidate2}"
        if "lula" not in matchup_names or "flavio" not in matchup_names:
            continue
        percent1 = matchup.get("percent1")
        percent2 = matchup.get("percent2")
        if not isinstance(percent1, int | float) or not isinstance(percent2, int | float):
            continue
        if "lula" in candidate1:
            matches.add((float(percent1), float(percent2)))
        else:
            matches.add((float(percent2), float(percent1)))
    if len(matches) != 1:
        return None
    return next(iter(matches))


def main() -> None:  # noqa: C901, PLR0912, PLR0915
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    remote = _git(args.repo, "remote", "get-url", "origin").strip().removesuffix(".git")
    if remote != _EXPECTED_REMOTE:
        raise SystemExit("unexpected Brazil poll source repository")
    _git(args.repo, "fsck", "--full", "--no-dangling")
    head = _git(args.repo, "rev-parse", "HEAD").strip()
    registry_raw = _git(args.repo, "show", f"{head}:polls/tse-registry.json")
    registry_payload = json.loads(registry_raw)
    registry_rows = registry_payload.get("records", registry_payload)
    if not isinstance(registry_rows, list):
        raise SystemExit("TSE registry shape is unsupported")
    registry = {
        _protocol_key(str(item["register_tse"])): item
        for item in registry_rows
        if isinstance(item, dict) and item.get("register_tse")
    }
    log = _git(
        args.repo,
        "log",
        "--reverse",
        "--format=%H%x09%cI",
        "--",
        _POLL_PATHSPEC,
    )
    versions: dict[str, set[tuple[float, float]]] = defaultdict(set)
    first_seen: dict[str, dict[str, object]] = {}
    rejection_counts: dict[str, int] = defaultdict(int)
    commits_scanned = 0
    files_scanned = 0
    for log_line in log.splitlines():
        commit, committed_at_raw = log_line.split("\t", 1)
        committed_at = datetime.fromisoformat(committed_at_raw).astimezone(UTC)
        changed = _git(
            args.repo,
            "diff-tree",
            "--root",
            "--no-commit-id",
            "--name-only",
            "-r",
            commit,
            "--",
            _POLL_PATHSPEC,
        )
        commits_scanned += 1
        for path in changed.splitlines():
            if not path.startswith("polls/polls-data-") or not path.endswith(".json"):
                continue
            raw = _git(args.repo, "show", f"{commit}:{path}")
            payload = json.loads(raw)
            polls = payload.get("polls")
            if not isinstance(polls, list):
                rejection_counts["invalid_snapshot_shape"] += 1
                continue
            files_scanned += 1
            for poll in polls:
                if not isinstance(poll, dict):
                    rejection_counts["invalid_poll_shape"] += 1
                    continue
                register = str(poll.get("register", ""))
                if not _REGISTER_PATTERN.fullmatch(register):
                    rejection_counts["no_exact_tse_protocol"] += 1
                    continue
                registry_row = registry.get(_protocol_key(register))
                if registry_row is None:
                    rejection_counts["protocol_absent_from_tse_registry"] += 1
                    continue
                if registry_row.get("scope") != "national":
                    rejection_counts["not_national_scope"] += 1
                    continue
                poll_date = str(poll.get("date", ""))
                if registry_row.get("publication_date") != poll_date:
                    rejection_counts["publication_date_mismatch"] += 1
                    continue
                runoff = _runoff_value(poll)
                if runoff is None:
                    rejection_counts["no_unique_numeric_lula_flavio_runoff"] += 1
                    continue
                lula, flavio = runoff
                versions[register].add(runoff)
                if register in first_seen:
                    continue
                first_seen[register] = {
                    "register_tse": register,
                    "institute": str(poll.get("institute", "")),
                    "poll_date": poll_date,
                    "sample": poll.get("sample"),
                    "reported_margin_error_pp": poll.get("margin"),
                    "lula_runoff_pct": lula,
                    "flavio_runoff_pct": flavio,
                    "lula_margin_pp": round(lula - flavio, 6),
                    "available_at": committed_at.isoformat(),
                    "source_commit": commit,
                    "source_path": path,
                    "source_blob": _git(args.repo, "rev-parse", f"{commit}:{path}").strip(),
                    "source_file_sha256": hashlib.sha256(raw.encode()).hexdigest(),
                    "tse_registry_scope_source": registry_row.get("scope_source"),
                }
    corrected = sorted(register for register, values in versions.items() if len(values) > 1)
    vintages = [item for register, item in first_seen.items() if register not in corrected]
    vintages.sort(key=lambda item: (str(item["available_at"]), str(item["register_tse"])))
    payload = {
        "schema": "chronos-brazil-runoff-poll-vintages/v1",
        "source_repository": remote,
        "source_head": head,
        "availability_rule": (
            "Exact Git committer timestamp of the earliest snapshot containing the "
            "numeric runoff result."
        ),
        "eligibility_rule": (
            "Exact BR-NNNNN/2026 protocol, current TSE registry match, AFOS national "
            "scope, publication-date match, unique numeric Lula-Flavio runoff, and no "
            "later numeric correction in retained history."
        ),
        "scale_rule": (
            "Runoff percentages and their margin are poll measurements, not "
            "Polymarket win probabilities."
        ),
        "registry_current_vintage_sha256": hashlib.sha256(registry_raw.encode()).hexdigest(),
        "commits_scanned": commits_scanned,
        "snapshot_files_scanned": files_scanned,
        "eligible_vintage_count": len(vintages),
        "corrected_protocols_excluded": corrected,
        "rejection_counts": dict(sorted(rejection_counts.items())),
        "vintages": vintages,
        "credentials_printed": False,
    }
    content = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode()
    try:
        with args.output.open("xb") as output:
            output.write(content)
    except FileExistsError:
        if args.output.read_bytes() != content:
            message = "Brazil poll-vintage receipt already contains different bytes"
            raise ValueError(message) from None
    print(
        json.dumps(
            {
                "status": "retained",
                "eligible_vintage_count": len(vintages),
                "corrected_protocol_count": len(corrected),
                "sha256": hashlib.sha256(content).hexdigest(),
                "output": str(args.output),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
