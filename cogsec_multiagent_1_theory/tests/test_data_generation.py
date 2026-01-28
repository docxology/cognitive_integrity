#!/usr/bin/env python3
"""Tests for data_generation.py module."""

import json
import tempfile
from pathlib import Path

import pytest


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
