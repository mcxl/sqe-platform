"""Source regressions only; actual action geometry requires the Mac UI tests."""

from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
VIEWS = ROOT / "ios/ACEClientApp/ACEClientApp/Views.swift"
UI_TESTS = ROOT / "ios/ACEClientApp/ACEClientAppUITests/ACEClientAppUITests.swift"


def test_each_shared_action_sizes_its_label_inside_the_button():
    source = VIEWS.read_text(encoding="utf-8")
    # Keep native Button behaviour. Size the label, not an inert outer wrapper.
    labels = re.findall(r"\} label: \{\s*Text\([^\n]+\)\s*"
                        r"\.frame\(minWidth: 44, minHeight: 44, alignment: \.leading\)\s*"
                        r"\.contentShape\(Rectangle\(\)\)\s*\}", source)
    assert len(labels) == 7
    assert source.count("Button {") == 7
    assert ".frame(width: 44, height: 44)" not in source


def test_ui_checks_measure_action_targets_without_suppressing_audits():
    source = UI_TESTS.read_text(encoding="utf-8")
    assert "private func assertMinimumActionTargets" in source
    assert "button.isHittable" in source
    assert "XCTAssertGreaterThanOrEqual(button.frame.width, 44" in source
    assert "XCTAssertGreaterThanOrEqual(button.frame.height, 44" in source
    assert source.count("assertMinimumActionTargets(in: app)") == 3
    assert source.count("try app.performAccessibilityAudit(for: .all)") == 1
    assert source.count("try assertAccessibilityAudit(in: app, scenario:") == 4
    assert source.count("performAccessibilityAudit") == 1
    for scenario in ('scenario: "configuration"', 'scenario: "signIn"', 'scenario: "release"', "scenario: scenario"):
        assert scenario in source
    assert "try? app.performAccessibilityAudit" not in source
    audit_helper = source.split("private func assertAccessibilityAudit", 1)[1]
    assert "ACE_A11Y_ISSUE" in audit_helper
    assert "return false" in audit_helper
    assert "return true" not in audit_helper
    assert "for identifier in approvedCopyControls" in source
    assert "XCTAssertEqual(copyButtons.count, approvedCopyControls.count" in source
    assert 'app.secureTextFields["Password"].exists' in source
