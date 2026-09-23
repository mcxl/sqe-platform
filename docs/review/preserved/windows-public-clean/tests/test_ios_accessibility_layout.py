"""Source checks for iOS accessibility layout repairs."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VIEWS = ROOT / "ios/ACEClientApp/ACEClientApp/Views.swift"
APP = ROOT / "ios/ACEClientApp/ACEClientApp/ACEClientAppApp.swift"


def test_sign_in_heading_is_an_ordinary_form_row_with_high_contrast_semantics():
    source = VIEWS.read_text(encoding="utf-8")
    sign_in = source.split("struct SignInView: View {", 1)[1].split(
        "struct CurrentReleaseMessageView", 1
    )[0]

    heading = '''Text("Sign In")
                .font(.title2)
                .bold()
                .foregroundStyle(.primary)
                .accessibilityAddTraits(.isHeader)
                .accessibilityIdentifier("Sign In heading")'''

    assert heading in sign_in
    assert f"{heading}\n            Section {{" in sign_in
    assert "header:" not in sign_in


def test_value_row_groups_label_and_wrapping_value_for_accessibility_geometry():
    source = VIEWS.read_text(encoding="utf-8")
    value_row = source.split("struct ValueRow: View {", 1)[1]

    assert "VStack(alignment: .leading, spacing: 4) {\n            VStack(alignment: .leading, spacing: 4)" in value_row
    assert "Text(field.label).font(.headline)" in value_row
    assert "Text(value)\n                    .frame(maxWidth: .infinity, alignment: .leading)" in value_row
    assert ".fixedSize(horizontal: false, vertical: true)" in value_row
    assert ".accessibilityElement(children: .combine)" in value_row
    assert '.accessibilityLabel("\\(field.label): \\(value)")' in value_row
    assert "Text(value).accessibilityLabel" not in value_row
    assert '.accessibilityLabel("Copy \\(field.label)")' in value_row


def test_appearance_indicator_uses_visible_safe_area_inset_during_ui_scenarios():
    source = APP.read_text(encoding="utf-8")
    app, indicator = source.split("private struct EffectiveInterfaceStyleIndicator: View {", 1)

    assert "if UITestScenario.current != nil {" in app
    assert ".safeAreaInset(edge: .top, spacing: 0)" in app
    assert "EffectiveInterfaceStyleIndicator()" in app
    assert ".opacity(" not in indicator
    assert ".foregroundStyle(.primary)" in indicator
    assert ".background(.background)" in indicator
    assert ".frame(maxWidth: .infinity, alignment: .leading)" in indicator
    assert 'Text(colorScheme == .dark ? "dark" : "light")' in indicator
    assert '.accessibilityIdentifier("Effective interface style")' in indicator
