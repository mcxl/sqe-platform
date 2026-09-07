import os
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from tools import diagnose_ios as diagnostic


def test_redaction_keeps_error_but_removes_private_values():
    with patch.dict(os.environ, {"PRIVATE_TEST_VALUE": "hidden-token-123"}):
        text = diagnostic.redact('error: hidden-token-123 /Users/builder/project/file.swift:18 user@host.invalid https://private.invalid token=secret')
    assert "error:" in text
    assert "hidden-token-123" not in text
    assert "/Users/" not in text
    assert "user@" not in text
    assert "https://" not in text
    assert "token=secret" not in text


def test_error_selection_retains_actual_failure(tmp_path):
    log = tmp_path / "ui.log"
    log.write_text('normal build output\nerror: XCTAssertEqual failed: light expected\n', encoding="utf-8")
    assert diagnostic.errors(log) == ["error: XCTAssertEqual failed: light expected"]


def test_missing_log_is_unknown(tmp_path):
    assert diagnostic.errors(tmp_path / "absent") == ["error log unavailable"]


def test_error_limit(tmp_path):
    log = tmp_path / "negative.log"
    log.write_text("\n".join(f"error: failure {n}" for n in range(100)), encoding="utf-8")
    assert len(diagnostic.errors(log)) == 30


def test_context_rejects_local_execution():
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValueError):
            diagnostic.context()


def test_exact_scope_and_retention_contract():
    source = Path(diagnostic.__file__).read_text(encoding="utf-8")
    yaml = (diagnostic.rt.ROOT / "codemagic.yaml").read_text(encoding="utf-8")
    section = yaml.split("  ace-ios-diagnostic-manual:", 1)[1].split("  ace-ios-core:", 1)[0]
    assert "max_build_duration: 15" in section
    assert "triggering:" not in section
    assert "- mcx19_diagnostic" in section
    assert "mcx19_live_evidence" not in section
    assert "/private/tmp/mcx-19-diagnostic-safe/diagnostic.json" in section
    assert "live-evidence --" not in section
    assert "ios_release_ui_matrix" not in source
    assert diagnostic.METHOD == "testBothAppearances"
    assert "ui_log, 360" in source


def test_diagnostic_runs_only_both_appearances_and_retains_failure(tmp_path, monkeypatch):
    """Catch an extra build, wrong selector/appearance, or lost assertion details."""
    root = tmp_path / "raw"
    safe = tmp_path / "safe"
    root.mkdir()
    safe.mkdir()
    monkeypatch.setattr(diagnostic, "ROOT", root)
    monkeypatch.setattr(diagnostic, "SAFE_ROOT", safe)
    monkeypatch.setattr(diagnostic, "context", lambda: "a" * 40)
    monkeypatch.setattr(diagnostic.rt, "_live_artifact_root", lambda path: path)
    monkeypatch.setattr(diagnostic.rt, "resolve_ios_destinations", lambda devices: {devices[0]: "platform=iOS Simulator,id=fixture"})
    commands = []

    def run(command, environment, log, timeout):
        commands.append(command)
        if command[:2] == ["xcodebuild", "test"]:
            assert "-only-testing:ACEClientAppUITests/ACEClientAppUITests/testBothAppearances" in command
            assert "ACE_UI_TEST_APPEARANCE=dark" in command
            assert environment["TEST_RUNNER_ACE_UI_TEST_APPEARANCE"] == "dark"
            assert timeout == 360
            (root / "ui.xcresult").mkdir()
            log.write_text('error: XCTAssertEqual failed: light is not dark\n')
            return {"processExit": 65}
        assert command[:4] == ["xcrun", "xcresulttool", "get", "test-results"]
        log.write_text(json.dumps({"passedTests": 0, "failedTests": 1, "skippedTests": 0,
            "testFailures": [{"failureText": "XCTAssertEqual failed: light is not dark"}]}))
        return {"processExit": 0}

    monkeypatch.setattr(diagnostic, "run", run)
    assert diagnostic.main() == 1
    report = json.loads((safe / "diagnostic.json").read_text())
    assert len(commands) == 2
    assert set(report["results"]) == {"ui"}
    assert report["releaseEvidence"] is False
    assert "light is not dark" in report["results"]["ui"]["testFailureDetails"]
