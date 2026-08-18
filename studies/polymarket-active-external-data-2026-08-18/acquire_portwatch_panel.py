# ruff: noqa: D103, E501, EM101, INP001, T201, TRY003

"""Retain a validated current-vintage panel of all PortWatch chokepoints."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlencode

from research_agent.data_workspace import DataWorkspace, DeriveStatus, FetchRequest, FetchStatus

_HOST = "services9.arcgis.com"
_BASE_URL = (
    "https://services9.arcgis.com/weJ1QsnbMYJlCHdG/ArcGIS/rest/services/"
    "Daily_Chokepoints_Data/FeatureServer/0/query"
)
_PAGE_SIZE = 5000
_OFFSETS = (0, 5000, 10000, 15000, 20000, 25000)
_EXPECTED_ROWS = 26852
_FIELDS = "ObjectId,date,portid,portname,n_tanker,n_cargo,n_total,capacity"
_TRANSFORM = """\
payload = json_input("source")
if "features" not in payload or "error" in payload:
    invalid = 1 / 0
features = payload["features"]
if len(features) < 1 or len(features) > int(param("page_size")):
    invalid = 1 / 0
object_ids = []
dates = []
portids = []
portnames = []
n_tanker = []
n_cargo = []
n_total = []
capacity = []
expected = set(["ObjectId", "date", "portid", "portname", "n_tanker", "n_cargo", "n_total", "capacity"])
last_object_id = -1
for feature in features:
    if set(feature) != set(["attributes"]):
        invalid = 1 / 0
    row = feature["attributes"]
    if set(row) != expected:
        invalid = 1 / 0
    object_id = int(row["ObjectId"])
    date = str(row["date"])
    portid = str(row["portid"])
    portname = str(row["portname"])
    tanker = int(row["n_tanker"])
    cargo = int(row["n_cargo"])
    total = int(row["n_total"])
    if object_id <= last_object_id or len(date) != 10 or len(portid) < 1 or len(portname) < 1:
        invalid = 1 / 0
    if total != tanker + cargo or total < 0:
        invalid = 1 / 0
    last_object_id = object_id
    object_ids = object_ids + [object_id]
    dates = dates + [date]
    portids = portids + [portid]
    portnames = portnames + [portname]
    n_tanker = n_tanker + [tanker]
    n_cargo = n_cargo + [cargo]
    n_total = n_total + [total]
    capacity = capacity + [int(row["capacity"])]
result = emit({
    "object_id": object_ids,
    "date": dates,
    "portid": portids,
    "portname": portnames,
    "n_tanker": n_tanker,
    "n_cargo": n_cargo,
    "n_total": n_total,
    "capacity": capacity,
})
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    workspace = DataWorkspace(args.workspace)
    acquired_at = datetime.now(UTC)
    pages: list[dict[str, object]] = []
    total_rows = 0
    for offset in _OFFSETS:
        query = {
            "where": "year>=2024",
            "outFields": _FIELDS,
            "returnGeometry": "false",
            "orderByFields": "ObjectId ASC",
            "resultRecordCount": str(_PAGE_SIZE),
            "maxRecordCountFactor": "5",
            "resultOffset": str(offset),
            "f": "json",
        }
        url = f"{_BASE_URL}?{urlencode(query)}"
        fetched = workspace.fetch(
            FetchRequest(
                url=url,
                headers={"Accept": "application/json", "User-Agent": "ChronosResearch/0.1"},
                max_response_bytes=8 * 1024 * 1024,
                timeout_seconds=30,
                allowed_redirect_hosts=(_HOST,),
                permit_redirects=False,
            )
        )
        if fetched.status is not FetchStatus.SUCCEEDED or fetched.snapshot_ref is None:
            raise SystemExit("PortWatch panel page acquisition failed")
        derived = workspace.derive(
            inputs={"source": fetched.snapshot_ref},
            source=_TRANSFORM,
            parameters={"page_size": _PAGE_SIZE},
        )
        if derived.status is not DeriveStatus.SUCCEEDED or derived.dataset_ref is None:
            raise SystemExit("PortWatch panel page derivation failed")
        values = workspace.read_derived_json(derived.dataset_ref)
        if not isinstance(values, dict) or not isinstance(values.get("date"), list):
            raise SystemExit("PortWatch panel derived page is malformed")
        row_count = len(values["date"])
        total_rows += row_count
        pages.append(
            {
                "offset": offset,
                "row_count": row_count,
                "source_ref": fetched.snapshot_ref.as_dict(),
                "derived_ref": derived.dataset_ref.as_dict(),
            }
        )
    if total_rows != _EXPECTED_ROWS:
        raise SystemExit("PortWatch panel changed during fixed acquisition")
    payload = {
        "schema": "chronos-portwatch-chokepoint-panel/v1",
        "status": "succeeded",
        "acquired_at": acquired_at.isoformat(),
        "where": "year>=2024",
        "row_count": total_rows,
        "page_size": _PAGE_SIZE,
        "pages": pages,
        "availability_rule": "The complete panel becomes available at acquired_at; historical publication vintages are not inferred.",
        "revision_rule": "Current ArcGIS vintage may revise earlier dates.",
        "transform_sha256": hashlib.sha256(_TRANSFORM.encode()).hexdigest(),
        "production_database_writes": False,
    }
    content = (json.dumps(payload, separators=(",", ":"), sort_keys=True) + "\n").encode()
    try:
        with args.receipt.open("xb") as output:
            output.write(content)
    except FileExistsError:
        if args.receipt.read_bytes() != content:
            raise ValueError("PortWatch panel receipt already contains different bytes") from None
    print(json.dumps(payload, sort_keys=True))


if __name__ == "__main__":
    main()
