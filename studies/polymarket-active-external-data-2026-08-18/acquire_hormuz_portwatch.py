# ruff: noqa: D103, E501, EM101, INP001, T201, TRY003

"""Retain and strictly derive the current official PortWatch Hormuz history."""

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
_FIELDS = (
    "date,year,month,day,portid,portname,n_container,n_dry_bulk,n_general_cargo,"
    "n_roro,n_tanker,n_cargo,n_total,capacity"
)
_TRANSFORM = """\
payload = json_input("source")
if "features" not in payload or "error" in payload:
    invalid = 1 / 0
features = payload["features"]
if len(features) < 300 or len(features) > 1000:
    invalid = 1 / 0
dates = []
years = []
months = []
days = []
n_container = []
n_dry_bulk = []
n_general_cargo = []
n_roro = []
n_tanker = []
n_cargo = []
n_total = []
capacity = []
last_date = ""
expected = set(["date", "year", "month", "day", "portid", "portname", "n_container", "n_dry_bulk", "n_general_cargo", "n_roro", "n_tanker", "n_cargo", "n_total", "capacity"])
for feature in features:
    if set(feature) != set(["attributes"]):
        invalid = 1 / 0
    row = feature["attributes"]
    if set(row) != expected:
        invalid = 1 / 0
    date = str(row["date"])
    total = int(row["n_total"])
    cargo = int(row["n_cargo"])
    tanker = int(row["n_tanker"])
    if row["portid"] != "chokepoint6" or row["portname"] != "Strait of Hormuz":
        invalid = 1 / 0
    if len(date) != 10 or date <= last_date or date[0:4] != str(row["year"]):
        invalid = 1 / 0
    if total != cargo + tanker or total < 0:
        invalid = 1 / 0
    last_date = date
    dates = dates + [date]
    years = years + [int(row["year"])]
    months = months + [int(row["month"])]
    days = days + [int(row["day"])]
    n_container = n_container + [int(row["n_container"])]
    n_dry_bulk = n_dry_bulk + [int(row["n_dry_bulk"])]
    n_general_cargo = n_general_cargo + [int(row["n_general_cargo"])]
    n_roro = n_roro + [int(row["n_roro"])]
    n_tanker = n_tanker + [tanker]
    n_cargo = n_cargo + [cargo]
    n_total = n_total + [total]
    capacity = capacity + [int(row["capacity"])]
result = emit({
    "date": dates,
    "year": years,
    "month": months,
    "day": days,
    "n_container": n_container,
    "n_dry_bulk": n_dry_bulk,
    "n_general_cargo": n_general_cargo,
    "n_roro": n_roro,
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
    parameters = {
        "where": "portid='chokepoint6' AND year>=2025",
        "outFields": _FIELDS,
        "returnGeometry": "false",
        "orderByFields": "date ASC",
        "resultRecordCount": "1000",
        "f": "json",
    }
    url = f"{_BASE_URL}?{urlencode(parameters)}"
    workspace = DataWorkspace(args.workspace)
    fetched_at = datetime.now(UTC)
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
        raise SystemExit("official PortWatch acquisition failed")
    derived = workspace.derive(
        inputs={"source": fetched.snapshot_ref}, source=_TRANSFORM, parameters={}
    )
    if derived.status is not DeriveStatus.SUCCEEDED or derived.dataset_ref is None:
        raise SystemExit("official PortWatch strict derivation failed")
    values = workspace.read_derived_json(derived.dataset_ref)
    if not isinstance(values, dict) or not isinstance(values.get("date"), list):
        raise SystemExit("derived PortWatch columns are malformed")
    dates = values["date"]
    payload = {
        "schema": "chronos-hormuz-portwatch-acquisition/v1",
        "status": "succeeded",
        "public_locator": url,
        "fetched_at": fetched_at.isoformat(),
        "source_ref": fetched.snapshot_ref.as_dict(),
        "derived_ref": derived.dataset_ref.as_dict(),
        "row_count": len(dates),
        "first_date": dates[0],
        "last_date": dates[-1],
        "availability_rule": "All rows become available together at fetched_at; no historical publication vintage is inferred.",
        "revision_rule": "Current ArcGIS vintage may revise earlier dates; retained bytes are immutable but do not reconstruct prior vintages.",
        "transform_sha256": hashlib.sha256(_TRANSFORM.encode()).hexdigest(),
        "production_database_writes": False,
    }
    content = (json.dumps(payload, separators=(",", ":"), sort_keys=True) + "\n").encode()
    try:
        with args.receipt.open("xb") as output:
            output.write(content)
    except FileExistsError:
        if args.receipt.read_bytes() != content:
            raise ValueError("PortWatch receipt already contains different bytes") from None
    print(json.dumps(payload, sort_keys=True))


if __name__ == "__main__":
    main()
