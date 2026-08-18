"""Build deterministic SVG figures from retained process-paper receipts."""

# ruff: noqa: D103, E501, INP001, PLR0913, Q000

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
STUDY = HERE.parent
FIGURES = HERE / "figures"


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def _svg_bar_chart(
    *,
    title: str,
    subtitle: str,
    labels: list[str],
    series: list[tuple[str, list[float], str]],
    output: Path,
    y_label: str,
) -> None:
    width, height = 960, 560
    left, right, top, bottom = 110, 40, 95, 120
    plot_w, plot_h = width - left - right, height - top - bottom
    maximum = max(value for _, values, _ in series for value in values) * 1.12
    group_w = plot_w / len(labels)
    bar_w = min(86.0, group_w * 0.72 / len(series))
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        f'<text x="{left}" y="38" font-family="sans-serif" font-size="24" font-weight="700">{html.escape(title)}</text>',
        f'<text x="{left}" y="66" font-family="sans-serif" font-size="14" fill="#555">{html.escape(subtitle)}</text>',
    ]
    for tick in range(6):
        value = maximum * tick / 5
        y = top + plot_h - plot_h * tick / 5
        parts.append(f'<line x1="{left}" y1="{y:.2f}" x2="{left + plot_w}" y2="{y:.2f}" stroke="#ddd"/>')
        parts.append(f'<text x="{left - 12}" y="{y + 5:.2f}" text-anchor="end" font-family="sans-serif" font-size="12">{value:.2f}</text>')
    for group, label in enumerate(labels):
        center = left + group_w * (group + 0.5)
        for index, (_, values, color) in enumerate(series):
            value = values[group]
            x = center - len(series) * bar_w / 2 + index * bar_w
            bar_h = plot_h * value / maximum
            y = top + plot_h - bar_h
            parts.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{bar_w - 4:.2f}" height="{bar_h:.2f}" fill="{color}" rx="2"/>')
            parts.append(f'<text x="{x + (bar_w - 4) / 2:.2f}" y="{y - 7:.2f}" text-anchor="middle" font-family="sans-serif" font-size="11">{value:.3f}</text>')
        parts.append(f'<text x="{center:.2f}" y="{top + plot_h + 28}" text-anchor="middle" font-family="sans-serif" font-size="13">{html.escape(label)}</text>')
    legend_y = height - 48
    for index, (name, _, color) in enumerate(series):
        x = left + index * 240
        parts.append(f'<rect x="{x}" y="{legend_y - 12}" width="16" height="16" fill="{color}"/>')
        parts.append(f'<text x="{x + 24}" y="{legend_y + 1}" font-family="sans-serif" font-size="13">{html.escape(name)}</text>')
    parts.append(f'<text transform="translate(24 {top + plot_h / 2}) rotate(-90)" text-anchor="middle" font-family="sans-serif" font-size="13">{html.escape(y_label)}</text>')
    parts.append('</svg>')
    output.write_text("\n".join(parts) + "\n")


def main() -> None:
    development = _load(STUDY / "development-receipts/12_composed_process_family_comparison.json")["details"]
    successor = _load(STUDY / "successor-corpus/development-receipts/13_frozen_process_successor_replay.json")["details"]
    formal = _load(STUDY / "development-receipts/14_formal_hurdle_arrival_freeze.json")["formal_summary"]
    FIGURES.mkdir(parents=True, exist_ok=True)

    labels = ["Diffusion", "Memoryless", "State", "State + path"]
    development_values = [
        development["bounded_diffusion"]["event_macro_mean_nll"],
        development["memoryless_hurdle"]["event_macro_mean_nll"],
        development["state_hurdle"]["event_macro_mean_nll"],
        development["full_hurdle_vs_state"]["event_macro_mean_nll"],
    ]
    successor_values = [
        successor["bounded_diffusion"]["event_macro_mean_nll"],
        successor["memoryless_hurdle"]["event_macro_mean_nll"],
        successor["state_hurdle"]["event_macro_mean_nll"],
        successor["full_hurdle_vs_state"]["event_macro_mean_nll"],
    ]
    _svg_bar_chart(
        title="Complete process-law comparison",
        subtitle="Lower event-macro interval negative log score is better",
        labels=labels,
        series=[
            ("Development", development_values, "#3465a4"),
            ("Later no-refit replay", successor_values, "#f28e2b"),
        ],
        output=FIGURES / "process-family-event-nll.svg",
        y_label="Event-macro NLL",
    )

    _svg_bar_chart(
        title="Formal arrival compression",
        subtitle="Fixed ceilings are 0.20 overall/event and 0.22 by chronological half",
        labels=["Observation", "Event macro", "Early events", "Late events"],
        series=[
            (
                "Observed Brier",
                [
                    formal["observation_mse"],
                    formal["event_macro_mse"],
                    formal["early_event_macro_mse"],
                    formal["late_event_macro_mse"],
                ],
                "#c44e52",
            )
        ],
        output=FIGURES / "formal-arrival-brier.svg",
        y_label="Brier / MSE",
    )


if __name__ == "__main__":
    main()
