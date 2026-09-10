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
    assert "isAtLeast44Points(button.frame.width)" in source
    assert "isAtLeast44Points(button.frame.height)" in source
    action_target_helper = source.split("private func isAtLeast44Points", 1)[1]
    assert "let minimum: CGFloat = 44" in action_target_helper
    assert "measurement >= minimum || minimum - measurement <= minimum.ulp * 8" in action_target_helper
    def method_source(name):
        body = source.split(f"func {name}(", 1)[1]
        return re.split(r"\n    (?:private )?func ", body, maxsplit=1)[0]

    action_methods = (
        "testSignInPasswordFieldIsSecure",
        "testFictionalReleaseHasApprovedCopyControls",
        "testAllControlledScenariosShowExpectedStateAndAudit",
        "testNormalDeviceSettings",
        "assertFullReleaseInformation",
    )
    for method in action_methods:
        assert "assertMinimumActionTargets(in: app)" in method_source(method)
    normal_method = method_source("testNormalDeviceSettings")
    assert "requiredNormalDeviceContentSize()" in normal_method
    assert 'NSPredicate(format: "value == %@", expectedContentSize)' in normal_method
    assert "ACE_UI_TEST_APPEARANCE" not in normal_method
    release_method = method_source("testFictionalReleaseHasApprovedCopyControls")
    assert 'ProcessInfo.processInfo.environment["ACE_UI_TEST_RETAIN_INITIAL_AUDIT_SCREENSHOT"] == "1"' in release_method
    assert '"Fictional release — initial-audit — \\(appearance)"' in release_method
    assert release_method.index("Fictional release — initial-audit") < release_method.index(
        'try assertAccessibilityAudit(in: app, scenario: "release-initial")'
    )
    assert source.count("try app.performAccessibilityAudit(for: .all, auditIssueHandler)") == 1
    audit_methods = (*action_methods[:4], "testLaunchShowsSafeConfigurationState")
    for method in audit_methods:
        assert "try assertAccessibilityAudit(in: app, scenario:" in method_source(method)
    assert source.count("performAccessibilityAudit") == 1
    for scenario in ('scenario: "configuration"', 'scenario: "signIn"', 'scenario: "release"', "scenario: scenario"):
        assert scenario in source
    assert "try? app.performAccessibilityAudit" not in source
    audit_helper = source.split("private func assertAccessibilityAudit", 1)[1]
    assert "ACE_A11Y_ISSUE" in audit_helper
    assert "let auditIssueHandler: @Sendable (XCUIAccessibilityAuditIssue) -> Bool" in audit_helper
    assert 'Self.accessibilityIssueJSON(issue, scenario: scenario)' in audit_helper
    assert 'self.accessibilityIssueJSON' not in audit_helper
    assert "private static func accessibilityIssueJSON" in source
    assert "private static func limitedAuditText" in source
    assert "return false" in audit_helper
    assert "return true" not in audit_helper
    assert "for identifier in approvedCopyControls" in source
    assert "XCTAssertEqual(copyButtons.count, approvedCopyControls.count" in source
    assert 'app.secureTextFields["Password"].exists' in source
