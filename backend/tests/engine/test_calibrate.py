"""Tests for app.engine.calibrate (TSK-017)."""

import pytest

from app.engine.calibrate import main, print_calibration_report, run_calibration


def test_run_calibration_returns_expected_structure() -> None:
    data = run_calibration()
    assert "trials" in data
    assert "summaries" in data
    assert "constants" in data

    summaries = {s.category: s for s in data["summaries"]}
    assert set(summaries.keys()) == {"identical", "clone_edits", "crop", "unrelated"}

    # Identical copies must be 100% match
    assert summaries["identical"].phash_min == 0
    assert summaries["identical"].phash_max == 0
    assert summaries["identical"].mean_sim == 100.0

    # Clone edits (recompress, downscale, watermark, recolor) maintain high similarity
    assert summaries["clone_edits"].mean_sim >= 95.0
    assert summaries["clone_edits"].phash_max <= 8

    # Crops demonstrate hash blind spot (10 to 28 bits)
    assert summaries["crop"].phash_min == 10
    assert summaries["crop"].phash_max == 28

    # Unrelated logos must strictly score 0.0% similarity
    assert summaries["unrelated"].mean_sim == 0.0
    assert summaries["unrelated"].phash_min >= 24


def test_print_calibration_report_runs_cleanly(capsys: pytest.CaptureFixture[str]) -> None:
    data = run_calibration()
    print_calibration_report(data)
    captured = capsys.readouterr().out

    assert "HALISI DETECTION ENGINE" in captured
    assert "EMPIRICAL DISTRIBUTION SUMMARY" in captured
    assert "KEY CALIBRATION FINDINGS" in captured
    assert "Crop Detection Boundary" in captured


def test_calibrate_main_executes(capsys: pytest.CaptureFixture[str]) -> None:
    main()
    captured = capsys.readouterr().out
    assert "TSK-017 Calibration Benchmarks" in captured
