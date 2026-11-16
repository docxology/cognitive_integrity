"""Detection Results module.

Part of the Cognitive Integrity Framework.
"""

#!/usr/bin/env python3
from __future__ import annotations

"""Detection results visualization module."""

import csv
import os

os.environ["MPLBACKEND"] = "Agg"

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from .utils import _load_json_data, _require_number


def create_detection_results_figure(output_dir: Path) -> Path:
    """
    Create a mixed measured/schematic figure from complete source artifacts.

    All three files under ``output_dir/data`` are required. Invalid evidence
    raises before a figure or output directory is created. Ablation/integrity
    inputs and latency overhead are illustrative models, not measurements.
    The PDF path is returned only after both PNG and PDF have been saved.
    """
    data_path = output_dir / "data" / "detection_results.json"
    data = _load_json_data(data_path)
    if not isinstance(data, dict) or not isinstance(data.get("defense_configurations"), list):
        raise ValueError(f"{data_path}: defense_configurations must be a list of named records")

    configs = {}
    for index, config in enumerate(data["defense_configurations"]):
        if not isinstance(config, dict) or not isinstance(config.get("name"), str):
            raise ValueError(f"{data_path}: defense_configurations[{index}] requires a name")
        name = config["name"]
        if name in configs:
            raise ValueError(f"{data_path}: duplicate defense configuration {name!r}")
        configs[name] = config

    pd_names = ["Baseline", "Firewall Only", "Full CIF"]
    attack_keys = ("prompt_injection", "trust_exploitation")
    config_rates = {}
    pd_detection = []
    pd_latency = []
    for name in pd_names:
        if name not in configs:
            raise ValueError(f"{data_path}: required defense configuration {name!r} is missing")
        config = configs[name]
        rates = config.get("detection_rates")
        if not isinstance(rates, dict) or any(key not in rates for key in attack_keys):
            raise ValueError(
                f"{data_path}: {name!r}.detection_rates requires "
                "prompt_injection and trust_exploitation"
            )
        validated_rates = {
            key: _require_number(value, data_path, f"{name}.detection_rates.{key}", maximum=1.0)
            for key, value in rates.items()
        }
        config_rates[name] = [validated_rates[key] for key in attack_keys]
        pd_detection.append(float(np.mean(list(validated_rates.values()))))
        pd_latency.append(
            _require_number(
                config.get("latency_overhead_pct"), data_path, f"{name}.latency_overhead_pct"
            )
        )

    ablation_path = output_dir / "data" / "ablation_study.json"
    ablation_data = _load_json_data(ablation_path)
    component_keys = (
        "full_cif",
        "minus_firewall",
        "minus_sandbox",
        "minus_tripwires",
        "minus_invariants",
        "minus_trust_decay",
    )
    if not isinstance(ablation_data, dict):
        raise ValueError(f"{ablation_path}: expected component records")
    detection = []
    for key in component_keys:
        component = ablation_data.get(key)
        if not isinstance(component, dict):
            raise ValueError(f"{ablation_path}: required component {key!r} is missing or malformed")
        detection.append(
            _require_number(
                component.get("detection"), ablation_path, f"{key}.detection", maximum=1.0
            )
        )
    components = ["Full CIF"] + [
        f"- {key.removeprefix('minus_').replace('_', ' ').title()}" for key in component_keys[1:]
    ]
    delta = [value - detection[0] for value in detection]

    integrity_path = output_dir / "data" / "integrity_timeseries.csv"
    attempts, baseline_integrity, firewall_integrity, full_cif_integrity = _load_integrity_data(
        integrity_path
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(2, 2, figsize=(14, 11))

    # Colorblind-friendly palette (IBM Design)
    # Accessible to deuteranopia, protanopia, and tritanopia
    colors = {
        "baseline": "#999999",
        "firewall": "#648FFF",
        "sandbox": "#785EF0",
        "tripwire": "#DC267F",
        "full_cif": "#FE6100",
    }


    # Panel A: Detection rate by attack type
    ax1 = axes[0, 0]
    # #11: only the categories the measured detection_results.json actually
    # carries (prompt_injection, trust_exploitation); the previous set listed
    # three categories the generator never produces, plotting constant-zero bars.
    attack_types = [
        "Prompt\nInjection",
        "Trust\nExploit",
    ]

    baseline = config_rates["Baseline"]
    firewall = config_rates["Firewall Only"]
    full_cif = config_rates["Full CIF"]

    x = np.arange(len(attack_types))
    width = 0.25

    ax1.bar(x - width, baseline, width, label="Baseline", color=colors["baseline"])
    ax1.bar(x, firewall, width, label="Firewall Only", color=colors["firewall"])
    ax1.bar(x + width, full_cif, width, label="Full CIF", color=colors["full_cif"])

    ax1.set_ylabel("Detection Rate", fontsize=11)
    ax1.set_title("A. Detection Rate by Attack Type", fontsize=12, fontweight="bold")
    ax1.set_xticks(x)
    ax1.set_xticklabels(attack_types, fontsize=9)
    ax1.legend(loc="upper right", fontsize=9)
    ax1.set_ylim(0, 1.1)
    ax1.grid(True, alpha=0.3, axis="y")

    # Panel B uses the producer's illustrative ablation inputs, never a fallback.
    ax2 = axes[0, 1]

    y_pos = np.arange(len(components))
    bars = ax2.barh(y_pos, detection, color=colors["full_cif"], alpha=0.8)

    # Color code by impact (colorblind-friendly)
    for i, (bar, d) in enumerate(zip(bars, delta)):
        if d < -0.1:
            bar.set_color("#DC267F")  # High impact - magenta
        elif d < -0.05:
            bar.set_color("#FE6100")  # Medium impact - orange
        elif d < 0:
            bar.set_color("#FFB000")  # Low impact - yellow

    ax2.set_yticks(y_pos)
    ax2.set_yticklabels(components, fontsize=10)
    ax2.set_xlabel("Detection Rate", fontsize=11)
    ax2.set_title("B. Ablation (illustrative, not measured)", fontsize=12, fontweight="bold")
    ax2.set_xlim(0, 1.05)
    ax2.grid(True, alpha=0.3, axis="x")

    # Add delta annotations
    for i, (d, det) in enumerate(zip(delta, detection)):
        if d != 0:
            ax2.text(det + 0.005, i, f"Δ={d:+.2f}", va="center", fontsize=9)

    # Panel C uses the supplied illustrative series, never invented samples.
    ax3 = axes[1, 0]

    ax3.plot(
        attempts,
        baseline_integrity,
        "s-",
        color=colors["baseline"],
        label="Baseline",
        linewidth=2,
        markersize=5,
    )
    ax3.plot(
        attempts,
        firewall_integrity,
        "^-",
        color=colors["firewall"],
        label="Firewall Only",
        linewidth=2,
        markersize=5,
    )
    ax3.plot(
        attempts,
        full_cif_integrity,
        "o-",
        color=colors["full_cif"],
        label="Full CIF",
        linewidth=2,
        markersize=5,
    )

    ax3.set_xlabel("Attack Attempts", fontsize=11)
    ax3.set_ylabel("Belief Integrity Score", fontsize=11)
    ax3.set_title("C. Integrity (illustrative, not measured)", fontsize=12, fontweight="bold")
    ax3.legend(loc="lower left", fontsize=9)
    ax3.set_ylim(0, 1.05)
    ax3.grid(True, alpha=0.3)

    # Panel D: Performance trade-off (Detection vs Latency)
    ax4 = axes[1, 1]

    # Detection comes from the artifact; latency is its declared model input.
    sizes = [100, 200, 300]

    scatter_colors = [
        colors["baseline"],
        colors["firewall"],
        colors["full_cif"],
    ]

    for det, lat, size, color, name in zip(
        pd_detection, pd_latency, sizes, scatter_colors, pd_names
    ):
        ax4.scatter(
            lat,
            det,
            s=size,
            c=color,
            alpha=0.8,
            edgecolors="black",
            linewidth=1.5,
            label=name,
        )
        ax4.annotate(name, (lat, det), xytext=(5, 5), textcoords="offset points", fontsize=9)

    ax4.set_xlabel("Latency Overhead (%, model; not measured)", fontsize=11)
    ax4.set_ylabel("Detection Rate", fontsize=11)
    ax4.set_title("D. Detection vs. Performance Trade-off", fontsize=12, fontweight="bold")
    ax4.set_ylim(-0.05, 1.05)
    ax4.grid(True, alpha=0.3)

    fig.text(
        0.5, 0.01,
        "A: corpus detection rates. B/C: illustrative, not measured. "
        "D: detection vs. model latency.",
        ha="center", fontsize=10,
    )
    plt.tight_layout(rect=[0, 0.04, 1, 1])

    output_path_png = output_dir / "detection_results.png"
    output_path_pdf = output_dir / "detection_results.pdf"

    plt.savefig(
        output_path_png,
        dpi=150,
        bbox_inches="tight",
        facecolor="white",
        edgecolor="none",
    )
    plt.savefig(output_path_pdf, bbox_inches="tight", facecolor="white", edgecolor="none")
    plt.close()

    print(str(output_path_png))
    print(str(output_path_pdf))
    return output_path_pdf


def _load_integrity_data(path: Path) -> tuple[list[int], list[float], list[float], list[float]]:
    """Validate the complete illustrative CSV before allocating a figure."""
    columns = ("baseline_integrity", "firewall_integrity", "full_cif_integrity")
    attempts: list[int] = []
    series: list[list[float]] = [[], [], []]
    try:
        with path.open(encoding="utf-8", newline="") as stream:
            reader = csv.DictReader(stream, strict=True)
            required = {"attack_attempt", *columns}
            if reader.fieldnames is None or not required.issubset(reader.fieldnames):
                raise ValueError(f"{path}: required CSV columns are {', '.join(sorted(required))}")
            if len(reader.fieldnames) != len(set(reader.fieldnames)):
                raise ValueError(f"{path}: duplicate CSV column names are not allowed")
            for line, row in enumerate(reader, start=2):
                if None in row:
                    raise ValueError(f"{path}: row {line} has more fields than the CSV header")
                try:
                    attempt = int(row["attack_attempt"])
                except (TypeError, ValueError) as exc:
                    raise ValueError(
                        f"{path}: row {line}.attack_attempt must be an integer"
                    ) from exc
                if attempt < 0 or (attempts and attempt <= attempts[-1]):
                    raise ValueError(
                        f"{path}: row {line}.attack_attempt must be nonnegative "
                        "and strictly increasing"
                    )
                attempts.append(attempt)
                for values, column in zip(series, columns):
                    try:
                        value = float(row[column])
                    except (TypeError, ValueError) as exc:
                        raise ValueError(f"{path}: row {line}.{column} must be numeric") from exc
                    values.append(
                        _require_number(value, path, f"row {line}.{column}", maximum=1.0)
                    )
    except FileNotFoundError as exc:
        raise FileNotFoundError(
            f"Required figure data not found: {path}. Supply the source artifact; "
            "no figure was generated."
        ) from exc
    except (csv.Error, UnicodeDecodeError) as exc:
        raise ValueError(f"Invalid CSV figure data in {path}: {exc}") from exc
    if not attempts:
        raise ValueError(f"{path}: integrity timeseries must contain at least one numeric row")
    return attempts, series[0], series[1], series[2]
