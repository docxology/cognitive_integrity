"""Check the existing trust arithmetic on a fixed, local mathematical fixture."""

from __future__ import annotations

import json
import sys
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "cogsec_multiagent_1_theory" / "src" / "trust.py"


def load_trust_module():
    spec = spec_from_file_location("trust_fixture_source", SOURCE)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load the checked-in trust module: {SOURCE}")
    module = module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def write_json(path: Path, payload: object) -> None:
    path.write_text(
        json.dumps(payload, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )


def main() -> None:
    source = load_trust_module()
    calculus = source.TrustCalculus(
        source.TrustConfig(alpha=0.25, beta=0.5, gamma=0.25, decay=0.5)
    )
    component_scores = [0.25, 0.5, 0.75]
    edges = [1.0, 0.75, 0.5]
    prefixes = [edges[: index + 1] for index in range(len(edges))]
    weighted_score = calculus.compute_trust(*component_scores)
    path_scores = [calculus.compute_path_trust(path) for path in prefixes]
    invalid_controls = {
        "non_finite_score": lambda: calculus.compute_trust(float("nan"), 0.5, 0.5),
        "negative_depth": lambda: calculus.delegate_trust(0.5, 0.5, depth=-1),
    }
    rejected = []
    for label, check in invalid_controls.items():
        try:
            check()
        except ValueError:
            rejected.append(label)
    if (
        weighted_score != 0.5
        or path_scores != [0.5, 0.1875, 0.0625]
        or rejected != list(invalid_controls)
    ):
        raise RuntimeError("The fixture no longer reproduces the documented checks.")

    output = ROOT / "output"
    data = output / "data"
    figures = output / "figures"
    data.mkdir(parents=True, exist_ok=True)
    figures.mkdir(parents=True, exist_ok=True)
    write_json(
        data / "trust_fixture.json",
        {
            "source": SOURCE.relative_to(ROOT).as_posix(),
            "component_scores": component_scores,
            "weights": [
                calculus.config.alpha,
                calculus.config.beta,
                calculus.config.gamma,
            ],
            "weighted_score": weighted_score,
            "decay": calculus.config.decay,
            "edge_scores": edges,
            "prefix_depths": [len(path) for path in prefixes],
            "prefix_scores": path_scores,
            "rejected_controls": rejected,
        },
    )

    figure = Figure(figsize=(6.2, 3.3), layout="constrained")
    FigureCanvasAgg(figure)
    axes = figure.subplots()
    depths = [len(path) for path in prefixes]
    axes.plot(depths, [min(path) for path in prefixes], "s--", label="Minimum edge")
    axes.plot(depths, path_scores, "o-", label="Delegated score")
    axes.set(
        xlabel="Prefix length in edges", ylabel="Score", ylim=(0, 1.05), xticks=depths
    )
    axes.legend()
    filename = "trust_fixture.png"
    figure.savefig(figures / filename, dpi=160)
    write_json(
        figures / "figure_registry.json",
        {
            "fig:trust-fixture": {
                "filename": filename,
                "caption": "Minimum edge scores and delegated scores for fixed path prefixes.",
                "alt_text": (
                    "Two labelled lines over three path prefixes. The delegated "
                    "score stays below the minimum edge score and decreases with depth."
                ),
            }
        },
    )


if __name__ == "__main__":
    main()
