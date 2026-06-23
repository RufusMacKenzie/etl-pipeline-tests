from pathlib import Path
import json
import pytest_check as check
from unittest.mock import mock_open, patch

from scripts.analyze_tests import post_github_comment, parse_test_results


PLACEHOLDER_TEXT = """
Lorem ipsum dolor sit amet, consectetur adipiscing elit, 
sed do eiusmod tempor incididunt ut labore et dolore magna
aliqua. Ut enim ad minim veniam, quis nostrud exercitation
ullamco laboris nisi ut aliquip ex ea commodo consequat. 
Duis aute irure dolor in reprehenderit in voluptate velit
esse cillum dolore eu fugiat nulla pariatur. Excepteur sint
occaecat cupidatat non proident, sunt in culpa qui officia
deserunt mollit anim id est laborum."""

MOCK_REPORT_ALL_PASSING = {
    "summary": {"total": 2, "passed": 2, "failed": 0, "duration": 0.1},
    "tests": [
        {
            "nodeid": "tests/test_foo.py::test_one",
            "outcome": "passed",
            "duration": 0.05,
        },
        {
            "nodeid": "tests/test_foo.py::test_two",
            "outcome": "passed",
            "duration": 0.05,
        },
    ],
}

MOCK_REPORT_WITH_FAILURE = {
    "summary": {"total": 2, "passed": 1, "failed": 1, "duration": 0.1},
    "tests": [
        {
            "nodeid": "tests/test_foo.py::test_one",
            "outcome": "passed",
            "duration": 0.05,
        },
        {
            "nodeid": "tests/test_foo.py::test_two",
            "outcome": "failed",
            "duration": 0.05,
            "call": {"longrepr": "AssertionError: expected True got False"},
        },
    ],
}


def test_post_github_comment_writes_to_summary_when_available(
    tmp_path, monkeypatch, capsys
):
    test_file = tmp_path / "summary.txt"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(test_file))

    post_github_comment(PLACEHOLDER_TEXT)
    captured = capsys.readouterr()
    assert "Analysis posted to job summary" in captured.out
    assert Path(test_file).is_file()

    found_expected_text = False
    with open(test_file, "r", encoding="utf-8") as file:
        if PLACEHOLDER_TEXT in file.read():
            found_expected_text = True
    assert found_expected_text


def test_post_github_comment_handles_missing_summary_file(monkeypatch, capsys):
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    post_github_comment(PLACEHOLDER_TEXT)
    captured = capsys.readouterr()
    assert "GITHUB_STEP_SUMMARY not available" in captured.out


def test_parse_results_all_passing_tmp_path(tmp_path):
    report_path = tmp_path / "mock_report.json"
    with open(report_path, "w") as file:
        json.dump(MOCK_REPORT_ALL_PASSING, file, indent=4)

    results = parse_test_results(report_path)
    check.equal(2, results["summary"]["total"])
    check.equal(2, results["summary"]["passed"])
    check.equal(0, results["summary"]["failed"])
    check.equal(2, len(results["passed"]))
    check.equal(0, len(results["failed"]))
    check.is_true("tests/test_foo.py::test_one" in results["passed"])


def test_parse_results_with_failure_tmp_path(tmp_path):
    report_path = tmp_path / "mock_report.json"
    with open(report_path, "w") as file:
        json.dump(MOCK_REPORT_WITH_FAILURE, file, indent=4)

    results = parse_test_results(report_path)
    check.equal(2, results["summary"]["total"])
    check.equal(1, results["summary"]["passed"])
    check.equal(1, results["summary"]["failed"])
    check.equal(1, len(results["passed"]))
    check.equal(1, len(results["failed"]))
    check.is_true("tests/test_foo.py::test_one" in results["passed"])
    check.is_true("tests/test_foo.py::test_two" in results["failed"][0]["test"])
    check.is_true("AssertionError" in results["failed"][0]["error"])


def test_parse_results_all_passing_mock(tmp_path):
    mock_data = json.dumps(MOCK_REPORT_ALL_PASSING)
    with patch("builtins.open", mock_open(read_data=mock_data)):
        results = parse_test_results("fake-path.json")
    check.equal(2, results["summary"]["total"])
    check.equal(2, results["summary"]["passed"])
    check.equal(0, results["summary"]["failed"])
    check.equal(2, len(results["passed"]))
    check.equal(0, len(results["failed"]))
    check.is_true("tests/test_foo.py::test_one" in results["passed"])


def test_parse_results_with_failure_mock(tmp_path):
    mock_data = json.dumps(MOCK_REPORT_WITH_FAILURE)
    with patch("builtins.open", mock_open(read_data=mock_data)):
        results = parse_test_results("fake-path.json")

    check.equal(2, results["summary"]["total"])
    check.equal(1, results["summary"]["passed"])
    check.equal(1, results["summary"]["failed"])
    check.equal(1, len(results["passed"]))
    check.equal(1, len(results["failed"]))
    check.is_true("tests/test_foo.py::test_one" in results["passed"])
    check.is_true("tests/test_foo.py::test_two" in results["failed"][0]["test"])
    check.is_true("AssertionError" in results["failed"][0]["error"])
