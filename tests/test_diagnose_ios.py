import os
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
    assert diagnostic.METHOD == "testLaunchShowsSafeConfigurationState"
    assert "negative_log, 120" in source
    assert "ui_log, 360" in source
