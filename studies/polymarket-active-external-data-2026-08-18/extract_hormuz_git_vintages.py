# ruff: noqa: D103, E501, EM101, INP001, S603, S607, T201, TRY003

"""Extract exact historical PortWatch publication vintages from OCHA's Git history."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

_EXPECTED_REMOTE = "https://github.com/OCHA-DAP/hdx-portwatch-viz.git"
_DATA_PATH = "data/ports.json"
_START = datetime.fromisoformat("2026-05-11T13:03:57.905316+00:00")
_END = datetime.fromisoformat("2026-08-18T19:53:14+00:00")


def _git(repo: Path, *arguments: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *arguments],
        check=True,
        capture_output=True,
        text=True,
    ).stdout


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    remote = _git(args.repo, "remote", "get-url", "origin").strip()
    if remote != _EXPECTED_REMOTE:
        raise SystemExit("unexpected PortWatch vintage repository")
    log = _git(
        args.repo,
        "log",
        "--all",
        "--format=%H%x09%cI%x09%s",
        "--",
        _DATA_PATH,
    )
    vintages: list[dict[str, object]] = []
    for line in reversed(log.splitlines()):
        commit, committed_at_raw, subject = line.split("\t", 2)
        committed_at = datetime.fromisoformat(committed_at_raw).astimezone(UTC)
        if not subject.startswith("Update data") or not _START <= committed_at <= _END:
            continue
        raw = _git(args.repo, "show", f"{commit}:{_DATA_PATH}")
        payload = json.loads(raw)
        series = payload["strait_data"]["Strait of Hormuz"]
        current = sorted(series["current"], key=lambda row: int(row["doy"]))
        if not current:
            raise ValueError("Hormuz vintage has no current-year observations")
        latest = current[-1]
        prior = next(
            (row for row in reversed(current[:-1]) if int(row["doy"]) <= int(latest["doy"]) - 7),
            None,
        )
        latest_date = datetime.strptime(series["latest_date"], "%d %b %Y").replace(tzinfo=UTC)
        latest_rolling7 = float(latest["roll7"])
        delta7 = None if prior is None else latest_rolling7 - float(prior["roll7"])
        vintages.append(
            {
                "commit": commit,
                "committed_at": committed_at.isoformat(),
                "subject": subject,
                "blob": _git(args.repo, "rev-parse", f"{commit}:{_DATA_PATH}").strip(),
                "file_sha256": hashlib.sha256(raw.encode()).hexdigest(),
                "latest_date": latest_date.date().isoformat(),
                "source_lag_days": (committed_at.date() - latest_date.date()).days,
                "rolling7": latest_rolling7,
                "delta7": delta7,
                "observed_current_year_days": len(current),
            }
        )
    if not vintages:
        raise SystemExit("no eligible historical PortWatch vintages")
    payload = {
        "schema": "chronos-hormuz-git-vintages/v1",
        "source_repository": remote,
        "source_path": _DATA_PATH,
        "availability_rule": "Git commit committer timestamp; values are read from that exact committed blob.",
        "selection_start": _START.isoformat(),
        "selection_end": _END.isoformat(),
        "vintage_count": len(vintages),
        "vintages": vintages,
        "credentials_printed": False,
    }
    content = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode()
    try:
        with args.output.open("xb") as output:
            output.write(content)
    except FileExistsError:
        if args.output.read_bytes() != content:
            raise ValueError("vintage receipt already contains different bytes") from None
    print(
        json.dumps(
            {
                "status": "retained",
                "vintage_count": len(vintages),
                "sha256": hashlib.sha256(content).hexdigest(),
                "output": str(args.output),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
