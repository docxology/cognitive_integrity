#!/usr/bin/env python3
"""Tests for data_generation.py module."""

import json
import tempfile
from pathlib import Path


class TestDataGeneration:
    """Tests for data generation functions."""

    def test_generate_experimental_data(self):
        """Test generate_experimental_data creates expected output files."""
        from src.data_generation import generate_experimental_data

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            generate_experimental_data(output_dir)

            # Check data directory was created
            data_dir = output_dir / "data"
            assert data_dir.exists()

            # Check for expected output files
            expected_files = [
                "detection_results.json",
                "scalability_results.json",
                "ablation_study.json",
                "roc_results.json",
            ]

            for filename in expected_files:
                filepath = data_dir / filename
                assert filepath.exists(), f"Missing expected file: {filename}"

                # Verify it's valid JSON
                with open(filepath) as f:
                    data = json.load(f)
                assert data is not None

    def test_generate_experimental_data_content(self):
        """Test generated data has expected structure."""
        from src.data_generation import generate_experimental_data

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            generate_experimental_data(output_dir)

            data_dir = output_dir / "data"

            # Check ablation study structure
            with open(data_dir / "ablation_study.json") as f:
                ablation = json.load(f)
            assert "full_cif" in ablation
            assert "detection" in ablation["full_cif"]
            assert "delta" in ablation["full_cif"]

            # Check scalability results structure
            with open(data_dir / "scalability_results.json") as f:
                scalability = json.load(f)
            assert isinstance(scalability, list)
            assert len(scalability) > 0
            assert "agent_count" in scalability[0]

    def test_generate_experimental_data_creates_directory(self):
        """Test generate_experimental_data creates nested directories."""
        from src.data_generation import generate_experimental_data

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "nested" / "output"
            generate_experimental_data(output_dir)

            assert output_dir.exists()
            assert (output_dir / "data").exists()

    def test_generation_is_byte_reproducible(self):
        """Generated artifacts are byte-identical across runs (P1-3).

        No wall-clock timestamps (metadata.timestamp pinned to null) and an
        analytic (non-timing) scalability model make regeneration
        deterministic for the fixed seed.
        """
        from src.data_generation import generate_experimental_data

        files = [
            "detection_results.json",
            "roc_results.json",
            "scalability_results.json",
            "ablation_study.json",
            "architecture_comparison.json",
            "integrity_timeseries.csv",
        ]
        runs = []
        for _ in range(2):
            with tempfile.TemporaryDirectory() as tmpdir:
                output_dir = Path(tmpdir)
                generate_experimental_data(output_dir)
                runs.append({f: (output_dir / "data" / f).read_bytes() for f in files})

        for f in files:
            assert runs[0][f] == runs[1][f], f"{f} is not byte-reproducible"

    def test_measured_detection_results_and_fpr(self):
        """Detection rates and FPR are measured, and canonical injection is caught (P1-1, P1-13)."""
        import json as json_mod

        from src.data_generation import generate_experimental_data

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            generate_experimental_data(output_dir)
            with open(output_dir / "data" / "detection_results.json") as f:
                data = json_mod.load(f)
            # FPR is measured on the benign corpus and reconciled with the
            # generator's own classifier (no hard-coded 0.12/0.06).
            for cfg in data["defense_configurations"]:
                assert "false_positive_rate" in cfg
                assert isinstance(cfg["false_positive_rate"], float)
            # The canonical injection phrase is now detected (P1-1), so a
            # firewall-enabled config must detect more than baseline.
            by_name = {c["name"]: c for c in data["defense_configurations"]}
            assert by_name["Firewall Only"]["detection_rates"]["prompt_injection"] > 0.0
            # Full CIF must differ from Firewall Only (P1-5): its added
            # trust-exploitation layer detects the trust corpus the base
            # firewall misses.
            assert by_name["Full CIF"]["detection_rates"]["trust_exploitation"] > 0.0
            assert (
                by_name["Full CIF"]["detection_rates"]
                != by_name["Firewall Only"]["detection_rates"]
            )
            # Deterministic: no wall-clock timestamp.
            assert data["metadata"]["timestamp"] is None

    def test_scalability_is_monotonic_and_analytic(self):
        """Scalability consensus latency is monotonic (P1-14)."""
        import json as json_mod

        from src.data_generation import generate_experimental_data

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            generate_experimental_data(output_dir)
            with open(output_dir / "data" / "scalability_results.json") as f:
                data = json_mod.load(f)
            latencies = [
                d["consensus_latency_ms"] for d in sorted(data, key=lambda d: d["agent_count"])
            ]
            # Strictly increasing with agent count (previous wall-clock data
            # decreased 2 -> 16 agents).
            assert all(latencies[i] < latencies[i + 1] for i in range(len(latencies) - 1))
