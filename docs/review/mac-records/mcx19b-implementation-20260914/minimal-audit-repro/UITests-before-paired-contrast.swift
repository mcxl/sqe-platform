import Foundation
import CoreGraphics
import XCTest

final class ACEClientAppUITests: XCTestCase {
    private struct CoverageSettings: Codable, Hashable {
        let appearance: String
        let contentSize: String
        let orientation: String
        let boldText: Bool
        let reduceMotion: Bool
        let increaseContrast: Bool

        var payload: [String: Any] {
            ["appearance": appearance, "contentSize": contentSize, "orientation": orientation,
             "boldText": boldText, "reduceMotion": reduceMotion, "increaseContrast": increaseContrast]
        }
    }

    private struct CoverageCase: Decodable {
        let id: String
        let scenario: String
        let settings: CoverageSettings
        let audit: Bool
    }

    private struct AccessibilitySettingsRequest: Decodable {
        let mode: String
        let orientation: String?
        let boldText: Bool?
        let reduceMotion: Bool?
        let increaseContrast: Bool?
    }

    func testCoverageBatch() {
        continueAfterFailure = false
        guard let cases = decodedCoverageCases(), !cases.isEmpty else { return }
        guard let settings = cases.first?.settings, cases.allSatisfy({ $0.settings == settings }) else {
            XCTFail("ACE_COVERAGE_CASES_JSON cases must use one setting batch")
            return
        }
        for coverageCase in cases where !runCoverageCase(coverageCase) { return }
    }

    func testConfigureAccessibilitySettings() {
        continueAfterFailure = false
        guard let request = decodedAccessibilitySettingsRequest(), ["read", "set"].contains(request.mode) else {
            XCTFail("ACE_ACCESSIBILITY_SETTINGS_JSON mode must be read or set")
            return
        }
        let initialApp = launchForCoverageObservation()
        guard let initial = observedSettings(in: initialApp) else { initialApp.terminate(); return }
        initialApp.terminate()
        if request.mode == "set" {
            guard let boldText = request.boldText, let reduceMotion = request.reduceMotion,
                  let increaseContrast = request.increaseContrast, let orientation = request.orientation,
                  ["portrait", "landscape"].contains(orientation) else {
                XCTFail("Set requests must include all accessibility flags and orientation")
                return
            }
            let requested = CoverageSettings(appearance: initial.appearance, contentSize: initial.contentSize,
                                             orientation: orientation, boldText: boldText,
                                             reduceMotion: reduceMotion, increaseContrast: increaseContrast)
            guard configureAccessibilitySettings(from: initial, to: requested) else { return }
            XCUIDevice.shared.orientation = orientation == "landscape" ? .landscapeLeft : .portrait
        }
        let app = launchForCoverageObservation()
        defer { app.terminate() }
        guard let observed = observedSettings(in: app) else { return }
        if request.mode == "set" {
            guard let boldText = request.boldText, let reduceMotion = request.reduceMotion,
                  let increaseContrast = request.increaseContrast, let orientation = request.orientation,
                  assertRequestedOrientation(in: app, requested: orientation),
                  requireCoverage(
                    observed.orientation == orientation && observed.boldText == boldText && observed.reduceMotion == reduceMotion
                        && observed.increaseContrast == increaseContrast,
                    "App accessibility flags do not match the requested native Settings values"
                  ) else { return }
        }
        emitJSON(marker: "ACE_SETTINGS_RESULT", payload: ["mode": request.mode, "observed": [
            "boldText": observed.boldText, "reduceMotion": observed.reduceMotion,
            "increaseContrast": observed.increaseContrast, "orientation": observed.orientation
        ]])
    }

    private func decodedCoverageCases() -> [CoverageCase]? {
        guard let value = ProcessInfo.processInfo.environment["ACE_COVERAGE_CASES_JSON"],
              let data = value.data(using: .utf8) else {
            XCTFail("ACE_COVERAGE_CASES_JSON is required")
            return nil
        }
        do { return try JSONDecoder().decode([CoverageCase].self, from: data) }
        catch { XCTFail("ACE_COVERAGE_CASES_JSON is invalid: \(error.localizedDescription)"); return nil }
    }

    private func decodedAccessibilitySettingsRequest() -> AccessibilitySettingsRequest? {
        guard let value = ProcessInfo.processInfo.environment["ACE_ACCESSIBILITY_SETTINGS_JSON"],
              let data = value.data(using: .utf8) else {
            XCTFail("ACE_ACCESSIBILITY_SETTINGS_JSON is required")
            return nil
        }
        do { return try JSONDecoder().decode(AccessibilitySettingsRequest.self, from: data) }
        catch { XCTFail("ACE_ACCESSIBILITY_SETTINGS_JSON is invalid: \(error.localizedDescription)"); return nil }
    }

    private func runCoverageCase(_ coverageCase: CoverageCase) -> Bool {
        guard ProcessInfo.processInfo.environment["ACE_UI_TEST_APPEARANCE"] == nil else {
            XCTFail("Coverage runs must not set ACE_UI_TEST_APPEARANCE")
            return false
        }
        guard requireCoverage(["light", "dark"].contains(coverageCase.settings.appearance)
            && ["portrait", "landscape"].contains(coverageCase.settings.orientation),
            "Unsupported coverage settings for \(coverageCase.id)") else { return false }
        XCUIDevice.shared.orientation = coverageCase.settings.orientation == "landscape" ? .landscapeLeft : .portrait
        let app = launchForCoverageObservation(scenario: coverageCase.scenario)
        defer { app.terminate() }
        guard waitForCoverageState(in: app, scenario: coverageCase.scenario),
              assertRequestedOrientation(in: app, requested: coverageCase.settings.orientation),
              let observed = observedSettings(in: app),
              requireCoverage(observed == coverageCase.settings,
                              "Observed settings differ from requested settings for \(coverageCase.id): \(observed.payload)") else { return false }
        var screenshots: [String] = []
        captureCoverageViewport(in: app, caseID: coverageCase.id, viewport: "initial", screenshots: &screenshots)
        var audits = 0
        if coverageCase.audit {
            guard runCoverageAudit(in: app, scenario: coverageCase.scenario, viewport: "initial") else { return false }
            audits += 1
        }
        guard verifyCoverageScenario(coverageCase.scenario, in: app, caseID: coverageCase.id,
                                     audit: coverageCase.audit, screenshots: &screenshots, audits: &audits) else { return false }
        emitJSON(marker: "ACE_CASE_RESULT", payload: ["id": coverageCase.id, "scenario": coverageCase.scenario,
            "observed": observed.payload, "result": "passed", "screenshots": screenshots, "auditInvocations": audits])
        return true
    }

    private func launchForCoverageObservation(scenario: String = "release") -> XCUIApplication {
        let app = XCUIApplication()
        app.launchEnvironment["ACE_UI_TEST_SCENARIO"] = scenario
        app.launchEnvironment["ACE_COVERAGE_OBSERVATIONS"] = "1"
        app.launchEnvironment.removeValue(forKey: "ACE_UI_TEST_APPEARANCE")
        app.launch()
        return app
    }

    private func observedSettings(in app: XCUIApplication) -> CoverageSettings? {
        let indicator = app.staticTexts["Effective interface style"]
        guard requireCoverage(indicator.waitForExistence(timeout: 5), "Coverage observation indicator must exist") else { return nil }
        let ready = XCTNSPredicateExpectation(predicate: NSPredicate { _, _ in
            guard let value = indicator.value as? String, let data = value.data(using: .utf8) else { return false }
            return (try? JSONDecoder().decode(CoverageSettings.self, from: data)) != nil
        }, object: nil)
        guard requireCoverage(XCTWaiter.wait(for: [ready], timeout: 5) == .completed,
                              "Coverage observation indicator must contain JSON"),
              let value = indicator.value as? String, let data = value.data(using: .utf8) else { return nil }
        do { return try JSONDecoder().decode(CoverageSettings.self, from: data) }
        catch { XCTFail("Coverage observation JSON is invalid: \(error.localizedDescription)"); return nil }
    }

    private func assertRequestedOrientation(in app: XCUIApplication, requested: String) -> Bool {
        let expectation = XCTNSPredicateExpectation(predicate: NSPredicate { _, _ in
            let frame = app.frame
            return requested == "landscape" ? frame.width > frame.height : frame.height > frame.width
        }, object: nil)
        return requireCoverage(XCTWaiter.wait(for: [expectation], timeout: 5) == .completed,
                               "App frame did not reach requested \(requested) orientation")
    }

    private func waitForCoverageState(in app: XCUIApplication, scenario: String) -> Bool {
        let expected: XCUIElement
        switch scenario {
        case "signIn": expected = app.staticTexts["Sign In heading"]
        case "loading": expected = app.progressIndicators["Loading"]
        case "release", "noConclusion", "noActions": expected = app.staticTexts["Current Release"]
        case "emptyRelease", "emptyEngagement": expected = coverageElement(in: app, labeled: "No current release is available.")
        case "denied": expected = coverageElement(in: app, labeled: "Access denied. Sign in again.")
        case "unavailable", "unexpected", "invalidResponse": expected = coverageElement(in: app, labeled: "ACE is unavailable. Try again later.")
        case "connection": expected = coverageElement(in: app, labeled: "ACE could not be reached. Check your connection and try again.")
        case "timeout": expected = coverageElement(in: app, labeled: "The request timed out. Try again.")
        case "keychainRead": expected = coverageElement(in: app, labeled: "Saved sign-in could not be read. Try again.")
        case "keychainWrite": expected = coverageElement(in: app, labeled: "Sign-in could not be saved. Try again.")
        case "keychainDeletion": expected = coverageElement(in: app, labeled: "Saved sign-in could not be removed. Try again.")
        case "copyConfirmation": expected = app.buttons["Copy Engagement name"]
        case "privacy": expected = coverageElement(in: app, labeled: "ACE Client")
        default: XCTFail("Unsupported coverage scenario: \(scenario)"); return false
        }
        return requireCoverage(expected.waitForExistence(timeout: 5), "Expected state is missing for \(scenario)")
            && requireCoverage(isFullyVisibleInApp(expected, app: app), "Expected state is not visible for \(scenario)")
    }

    private func verifyCoverageScenario(_ scenario: String, in app: XCUIApplication, caseID: String, audit: Bool,
                                        screenshots: inout [String], audits: inout Int) -> Bool {
        switch scenario {
        case "release":
            return traverseReleaseFields(releaseFields, in: app, caseID: caseID, screenshots: &screenshots)
                && verifyReleaseActions(releaseFields, in: app)
                && captureAndAudit(in: app, scenario: scenario, caseID: caseID, viewport: "release-final", audit: audit, screenshots: &screenshots, audits: &audits)
        case "noConclusion":
            let fields = releaseFields.filter { !$0.0.hasPrefix("Conclusion") && $0.0 != "Evidence reference" }
            return traverseReleaseFields(fields, in: app, caseID: caseID, screenshots: &screenshots)
                && verifyReleaseActions(fields, in: app)
                && verifyRequiredNotice("No conclusion is available.", scenario: scenario, in: app, caseID: caseID, viewport: "no-conclusion-notice", audit: audit, screenshots: &screenshots, audits: &audits)
        case "noActions":
            let fields = releaseFields.filter { !$0.0.hasPrefix("Action") }
            return traverseReleaseFields(fields, in: app, caseID: caseID, screenshots: &screenshots)
                && verifyReleaseActions(fields, in: app)
                && verifyRequiredNotice("No actions are available.", scenario: scenario, in: app, caseID: caseID, viewport: "no-actions-notice", audit: audit, screenshots: &screenshots, audits: &audits)
        case "copyConfirmation":
            let copy = app.buttons["Copy Engagement name"]
            guard verifyActionTarget(copy, name: "Copy Engagement name") else { return false }
            copy.tap()
            let confirmation = coverageElement(in: app, labeled: "Copied Engagement name.")
            guard requireCoverage(confirmation.waitForExistence(timeout: 5), "Copy confirmation is missing") else { return false }
            scrollUntilVisible(confirmation, in: app, field: "Copy confirmation")
            guard requireCoverage(isFullyVisible(confirmation, in: app.scrollViews.firstMatch), "Copy confirmation must be visible") else { return false }
            return captureAndAudit(in: app, scenario: scenario, caseID: caseID, viewport: "copy-confirmation", audit: audit, screenshots: &screenshots, audits: &audits)
        case "signIn":
            return requireCoverage(app.secureTextFields["Password"].exists, "Password must be a secure field")
                && verifyScenarioActionTargets(
                    coverageActionLabels(for: scenario),
                    in: app,
                    caseID: caseID,
                    screenshots: &screenshots
                )
        default:
            return verifyScenarioActionTargets(
                coverageActionLabels(for: scenario),
                in: app,
                caseID: caseID,
                screenshots: &screenshots
            )
        }
    }

    private func traverseReleaseFields(_ fields: [(String, String)], in app: XCUIApplication, caseID: String,
                                       screenshots: inout [String]) -> Bool {
        for (field, value) in fields {
            let row = coverageElement(in: app, labeled: "\(field): \(value)")
            scrollUntilVisible(row, in: app, field: field)
            guard requireCoverage(isFullyVisible(row, in: app.scrollViews.firstMatch), "Release value for \(field) must be visible") else { return false }
            captureCoverageViewport(in: app, caseID: caseID, viewport: "value-\(field)", screenshots: &screenshots)
            let copy = app.buttons["Copy \(field)"]
            scrollUntilVisible(copy, in: app, field: "Copy \(field)")
            guard verifyActionTarget(copy, name: "Copy \(field)") else { return false }
        }
        return true
    }

    private func verifyReleaseActions(_ fields: [(String, String)], in app: XCUIApplication) -> Bool {
        for label in fields.map({ "Copy \($0.0)" }) + ["Refresh current release", "Sign out"] {
            let button = app.buttons[label]
            scrollUntilVisible(button, in: app, field: label)
            guard verifyActionTarget(button, name: label) else { return false }
        }
        return true
    }

    private func verifyRequiredNotice(_ notice: String, scenario: String, in app: XCUIApplication, caseID: String, viewport: String,
                                      audit: Bool, screenshots: inout [String], audits: inout Int) -> Bool {
        let element = coverageElement(in: app, labeled: notice)
        scrollUntilVisible(element, in: app, field: notice)
        guard requireCoverage(isFullyVisible(element, in: app.scrollViews.firstMatch), "\(notice) must be visible") else { return false }
        return captureAndAudit(in: app, scenario: scenario, caseID: caseID, viewport: viewport, audit: audit, screenshots: &screenshots, audits: &audits)
    }

    private func captureAndAudit(in app: XCUIApplication, scenario: String, caseID: String, viewport: String,
                                 audit: Bool, screenshots: inout [String], audits: inout Int) -> Bool {
        captureCoverageViewport(in: app, caseID: caseID, viewport: viewport, screenshots: &screenshots)
        guard audit else { return true }
        guard runCoverageAudit(in: app, scenario: scenario, viewport: viewport) else { return false }
        audits += 1
        return true
    }

    private func coverageActionLabels(for scenario: String) -> [String] {
        switch scenario {
        case "signIn":
            return ["Sign in"]
        case "emptyRelease", "emptyEngagement", "unavailable", "unexpected", "connection", "timeout", "invalidResponse":
            return ["Refresh"]
        case "keychainRead", "keychainDeletion":
            return ["Try again"]
        default:
            return []
        }
    }

    private func verifyScenarioActionTargets(_ labels: [String], in app: XCUIApplication, caseID: String,
                                              screenshots: inout [String]) -> Bool {
        for label in labels {
            let button = app.buttons[label]
            guard requireCoverage(scrollControlIntoView(button, in: app, field: label),
                                  "Required control \(label) must become fully visible"),
                  verifyActionTarget(button, name: label) else { return false }
            captureCoverageViewport(in: app, caseID: caseID, viewport: "control-\(label)", screenshots: &screenshots)
        }
        return true
    }

    private func scrollControlIntoView(_ control: XCUIElement, in app: XCUIApplication, field: String) -> Bool {
        if isFullyVisibleInApp(control, app: app) && control.isHittable { return true }
        let scrollView = app.scrollViews.firstMatch
        if scrollView.exists {
            scrollUntilVisible(control, in: app, field: field)
            return isFullyVisible(control, in: scrollView)
        }
        let table = app.tables.firstMatch
        guard table.exists else { return false }
        for _ in 0..<16 {
            if isFullyVisible(control, in: table) { return true }
            let controlFrame = control.exists ? control.frame : .zero
            drag(table, upward: !control.exists || controlFrame == .zero || controlFrame.maxY > table.frame.maxY)
        }
        return isFullyVisible(control, in: table)
    }

    private func verifyActionTarget(_ button: XCUIElement, name: String) -> Bool {
        requireCoverage(button.exists && button.isHittable, "\(name) must be reachable")
            && requireCoverage(isAtLeast44Points(button.frame.width), "\(name) width is below 44 points")
            && requireCoverage(isAtLeast44Points(button.frame.height), "\(name) height is below 44 points")
    }

    private func coverageElement(in app: XCUIApplication, labeled label: String) -> XCUIElement {
        app.descendants(matching: .any).matching(NSPredicate(format: "label == %@", label)).firstMatch
    }

    private func isFullyVisibleInApp(_ element: XCUIElement, app: XCUIApplication) -> Bool {
        let frame = element.frame
        return frame.width > 0 && frame.height > 0 && app.frame.contains(frame)
    }

    private func captureCoverageViewport(in app: XCUIApplication, caseID: String, viewport: String,
                                         screenshots: inout [String]) {
        let name = "Coverage \(caseID) viewport \(viewport)"
        addScreenshot(of: app, named: name)
        screenshots.append(name)
    }

    private func runCoverageAudit(in app: XCUIApplication, scenario: String, viewport: String) -> Bool {
        do { try assertAccessibilityAudit(in: app, scenario: "\(scenario)-\(viewport)"); return true }
        catch { XCTFail("Accessibility audit failed for \(scenario) \(viewport): \(error.localizedDescription)"); return false }
    }

    private func requireCoverage(_ condition: @autoclosure () -> Bool, _ message: @autoclosure () -> String) -> Bool {
        guard condition() else { XCTFail(message()); return false }
        return true
    }

    private func emitJSON(marker: String, payload: [String: Any]) {
        guard let data = try? JSONSerialization.data(withJSONObject: payload, options: [.sortedKeys]),
              let value = String(data: data, encoding: .utf8) else { XCTFail("Could not serialize \(marker)"); return }
        print("\(marker) \(value)")
    }

    private func configureAccessibilitySettings(from observed: CoverageSettings, to requested: CoverageSettings) -> Bool {
        if observed.boldText == requested.boldText && observed.reduceMotion == requested.reduceMotion
            && observed.increaseContrast == requested.increaseContrast { return true }
        let settings = XCUIApplication(bundleIdentifier: "com.apple.Preferences")
        settings.activate()
        guard requireCoverage(settings.wait(for: .runningForeground, timeout: 5), "Settings did not open") else { return false }
        let changes: [(String, [String], Bool, Bool)] = [
            ("Bold Text", ["Accessibility", "Display & Text Size"], observed.boldText, requested.boldText),
            ("Reduce Motion", ["Accessibility", "Motion"], observed.reduceMotion, requested.reduceMotion),
            ("Increase Contrast", ["Accessibility", "Display & Text Size"], observed.increaseContrast, requested.increaseContrast)
        ]
        for (label, path, current, desired) in changes where current != desired {
            guard setNativeAccessibilityToggle(label, path: path, enabled: desired, in: settings) else { return false }
        }
        return true
    }

    private func setNativeAccessibilityToggle(_ label: String, path: [String], enabled: Bool, in settings: XCUIApplication) -> Bool {
        guard returnToSettingsRoot(settings) else {
            addScreenshot(of: settings, named: "Accessibility settings missing root")
            XCTFail("Settings root is unavailable")
            return false
        }
        for item in path where !tapSettingsItem(item, in: settings) {
            addScreenshot(of: settings, named: "Accessibility settings missing \(item)")
            XCTFail("Missing Settings control: \(item)")
            return false
        }
        let toggle = settings.switches[label]
        guard toggle.waitForExistence(timeout: 5), let current = nativeSwitchValue(toggle) else {
            addScreenshot(of: settings, named: "Accessibility settings missing \(label)")
            XCTFail("Missing Settings control: \(label)")
            return false
        }
        // Settings exposes the whole row as a Switch. A centre tap misses the visible switch.
        print("ACE_NATIVE_SWITCH \(label) before=\(current) expected=\(enabled) frame=\(toggle.frame)")
        if current != enabled {
            toggle.coordinate(withNormalizedOffset: CGVector(dx: 0.9, dy: 0.5)).tap()
        }
        let changed = XCTNSPredicateExpectation(predicate: NSPredicate { _, _ in self.nativeSwitchValue(toggle) == enabled }, object: nil)
        let reached = XCTWaiter.wait(for: [changed], timeout: 5) == .completed
        guard reached else {
            addScreenshot(of: settings, named: "Accessibility settings \(label) did not change")
            XCTFail("Settings control \(label): expected \(enabled), actual \(String(describing: nativeSwitchValue(toggle)))")
            return false
        }
        return true
    }

    private func returnToSettingsRoot(_ settings: XCUIApplication) -> Bool {
        for _ in 0..<8 {
            if settings.navigationBars["Settings"].exists { return true }
            let back = settings.navigationBars.buttons.firstMatch
            guard back.exists && back.isHittable else { return false }
            back.tap()
        }
        return settings.navigationBars["Settings"].exists
    }

    private func tapSettingsItem(_ label: String, in settings: XCUIApplication) -> Bool {
        for _ in 0..<12 {
            let candidates = [settings.cells[label], settings.staticTexts[label], settings.buttons[label]]
            if let candidate = candidates.first(where: { $0.exists && $0.isHittable }) { candidate.tap(); return true }
            settings.swipeUp()
        }
        return false
    }

    private func nativeSwitchValue(_ toggle: XCUIElement) -> Bool? {
        guard let value = toggle.value as? String else { return nil }
        switch value.lowercased() {
        case "1", "true", "on": return true
        case "0", "false", "off": return false
        default: return nil
        }
    }

    private var releaseFields: [(String, String)] {
        [("Engagement name", "Fictional Engagement"), ("Review status", "RELEASED"), ("Release version", "1"),
         ("Published date and time", "2026-08-24T10:15:30Z"), ("Conclusion title", "Fictional conclusion"),
         ("Conclusion summary", "Fictional summary"), ("Evidence reference", "FICTIONAL-REF-001"),
         ("Action description", "Fictional action"), ("Action owner", "Fictional owner"),
         ("Action target date", "2026-08-25"), ("Action status", "OPEN")]
    }

    private func requiredAppearance() -> String {
        guard let appearance = ProcessInfo.processInfo.environment["ACE_UI_TEST_APPEARANCE"],
              ["light", "dark"].contains(appearance) else {
            XCTFail("ACE_UI_TEST_APPEARANCE must be light or dark")
            return "light"
        }
        return appearance
    }

    private func launch(_ scenario: String, appearance requestedAppearance: String? = nil) -> XCUIApplication {
        let app = XCUIApplication()
        let appearance = requestedAppearance ?? requiredAppearance()
        app.launchEnvironment["ACE_UI_TEST_SCENARIO"] = scenario
        app.launchEnvironment["ACE_UI_TEST_APPEARANCE"] = appearance
        app.launch()
        return app
    }

    private func launchWithNormalDeviceSettings(_ scenario: String) -> XCUIApplication {
        XCTAssertNil(
            ProcessInfo.processInfo.environment["ACE_UI_TEST_APPEARANCE"],
            "Normal-device evidence must not receive a forced appearance"
        )
        let app = XCUIApplication()
        app.launchEnvironment["ACE_UI_TEST_SCENARIO"] = scenario
        app.launchEnvironment.removeValue(forKey: "ACE_UI_TEST_APPEARANCE")
        XCTAssertNil(
            app.launchEnvironment["ACE_UI_TEST_APPEARANCE"],
            "Normal-device launch must omit ACE_UI_TEST_APPEARANCE"
        )
        app.launch()
        return app
    }

    private func requiredNormalDeviceAppearance() -> String {
        guard let appearance = ProcessInfo.processInfo.environment["ACE_EXPECTED_EFFECTIVE_INTERFACE_STYLE"],
              ["light", "dark"].contains(appearance) else {
            XCTFail("ACE_EXPECTED_EFFECTIVE_INTERFACE_STYLE must be light or dark")
            return "light"
        }
        return appearance
    }

    private func requiredNormalDeviceContentSize() -> String {
        let supported = [
            "extra-small", "small", "medium", "large", "extra-large",
            "extra-extra-large", "extra-extra-extra-large", "accessibility-medium",
            "accessibility-large", "accessibility-extra-large",
            "accessibility-extra-extra-large", "accessibility-extra-extra-extra-large"
        ]
        guard let contentSize = ProcessInfo.processInfo.environment["ACE_EXPECTED_CONTENT_SIZE_CATEGORY"],
              supported.contains(contentSize) else {
            XCTFail("ACE_EXPECTED_CONTENT_SIZE_CATEGORY must be supported")
            return "medium"
        }
        return contentSize
    }

    func testBothAppearances() {
        for appearance in ["light", "dark"] {
            let app = launch("release", appearance: appearance)
            let indicator = app.staticTexts["Effective interface style"]
            XCTAssertTrue(indicator.waitForExistence(timeout: 5), "Appearance indicator must exist")
            let displayedAppearance = XCTNSPredicateExpectation(
                predicate: NSPredicate(format: "label == %@", appearance), object: indicator
            )
            XCTAssertEqual(XCTWaiter.wait(for: [displayedAppearance], timeout: 5), .completed,
                           "The displayed view must use \(appearance) appearance")
            XCTAssertTrue(app.staticTexts["FICTIONAL PILOT — CONTROLLED"].exists)
            addScreenshot(of: app, named: "Fictional release — forced-\(appearance)")
            app.terminate()
        }
    }

    func testLaunchShowsSafeConfigurationState() throws {
        let app = launch("configuration")
        XCTAssertTrue(app.staticTexts["This app is not configured for access."].exists)
        addScreenshot(of: app, named: "Controlled state — configuration — \(requiredAppearance())")
        try assertAccessibilityAudit(in: app, scenario: "configuration")
    }

    func testSignInPasswordFieldIsSecure() throws {
        let app = launch("signIn")
        let heading = app.staticTexts["Sign In heading"]
        XCTAssertTrue(heading.exists)
        XCTAssertEqual(heading.label, "Sign In")
        XCTAssertTrue(app.secureTextFields["Password"].exists)
        assertMinimumActionTargets(in: app)
        addScreenshot(of: app, named: "Controlled state — signIn — \(requiredAppearance())")
        try assertAccessibilityAudit(in: app, scenario: "signIn")
    }

    func testFictionalReleaseHasApprovedCopyControls() throws {
        let app = launch("release")
        let approvedCopyControls = [
            "Copy Engagement name", "Copy Review status", "Copy Release version", "Copy Published date and time",
            "Copy Conclusion title", "Copy Conclusion summary", "Copy Evidence reference", "Copy Action description",
            "Copy Action owner", "Copy Action target date", "Copy Action status"
        ]
        for identifier in approvedCopyControls { XCTAssertTrue(app.buttons[identifier].exists, identifier) }
        let copyButtons = app.buttons.matching(NSPredicate(format: "label BEGINSWITH %@", "Copy "))
        XCTAssertEqual(copyButtons.count, approvedCopyControls.count, "The release screen must not expose an unapproved copy control")
        assertMinimumActionTargets(in: app)
        let appearance = requiredAppearance()
        let indicator = app.staticTexts["Effective interface style"]
        XCTAssertTrue(indicator.waitForExistence(timeout: 5), "Appearance indicator must exist")
        let displayedAppearance = XCTNSPredicateExpectation(
            predicate: NSPredicate(format: "label == %@", appearance), object: indicator
        )
        XCTAssertEqual(
            XCTWaiter.wait(for: [displayedAppearance], timeout: 5),
            .completed,
            "The displayed view must use \(appearance) appearance before the initial audit"
        )
        if ProcessInfo.processInfo.environment["ACE_UI_TEST_RETAIN_INITIAL_AUDIT_SCREENSHOT"] == "1" {
            addScreenshot(of: app, named: "Fictional release — initial-audit — \(appearance)")
        }
        try assertAccessibilityAudit(in: app, scenario: "release-initial")
        assertFullReleaseInformation(in: app, appearance: appearance)
        assertMinimumActionTargets(in: app)
        addScreenshot(of: app, named: "Fictional release — approved-controls — \(appearance)")
        assertReleaseContrastProbeFramesAreStable(in: app)
        do {
            let preAuditFrames = releaseContrastProbeFrames(in: app)
            print("ACE_MCX19_ALL_AUDIT_PRE \(Self.releaseContrastProbeJSON(before: preAuditFrames, after: preAuditFrames))")
            defer {
                let postAuditFrames = releaseContrastProbeFrames(in: app)
                print("ACE_MCX19_ALL_AUDIT_POST \(Self.releaseContrastProbeJSON(before: postAuditFrames, after: postAuditFrames))")
            }
            try assertAccessibilityAudit(in: app, scenario: "release")
        }
        app.terminate()

        let confirmationApp = launch("copyConfirmation")
        confirmationApp.buttons["Copy Engagement name"].tap()
        XCTAssertTrue(confirmationApp.staticTexts["Copied Engagement name."].exists, "Copy confirmation must be available to VoiceOver")
        scrollUntilVisible(confirmationApp.staticTexts["Copied Engagement name."], in: confirmationApp, field: "Copy confirmation")
        addScreenshot(of: confirmationApp, named: "Controlled state — copyConfirmation — \(appearance)")
        try assertAccessibilityAudit(in: confirmationApp, scenario: "copyConfirmation-after-copy")
        confirmationApp.terminate()
    }

    func testClippingNoActionsStandaloneAudit() throws {
        try runOriginalScenarioAudit(scenario: "noActions", expected: "No actions are available.")
    }

    func testClippingNoConclusionStandaloneAudit() throws {
        try runOriginalScenarioAudit(scenario: "noConclusion", expected: "No conclusion is available.")
    }

    func testMinimalAuditReproAllAudits() throws {
        let app = launch("minimalAuditRepro")
        defer { app.terminate() }
        let bottom = app.staticTexts["Minimal audit reproduction bottom"]
        XCTAssertTrue(bottom.waitForExistence(timeout: 5), "Minimal audit reproduction must exist")
        assertMinimumActionTargets(in: app)
        try assertAccessibilityAudit(in: app, scenario: "minimal-audit-repro-initial")
        scrollUntilVisible(bottom, in: app, field: "Minimal audit reproduction bottom")
        XCTAssertTrue(
            isFullyVisible(bottom, in: app.scrollViews.firstMatch),
            "Minimal audit reproduction bottom must become fully visible after scrolling"
        )
        assertMinimumActionTargets(in: app)
        addScreenshot(of: app, named: "Minimal audit reproduction — post-scroll — \(requiredAppearance())")
        try assertAccessibilityAudit(in: app, scenario: "minimal-audit-repro-post-scroll")
    }

    func testMinimalAuditReproContrastOnlyAfterScroll() throws {
        let app = launch("minimalAuditRepro")
        defer { app.terminate() }
        let bottom = app.staticTexts["Minimal audit reproduction bottom"]
        XCTAssertTrue(bottom.waitForExistence(timeout: 5), "Minimal audit reproduction must exist")
        scrollUntilVisible(bottom, in: app, field: "Minimal audit reproduction bottom")
        XCTAssertTrue(
            isFullyVisible(bottom, in: app.scrollViews.firstMatch),
            "Minimal audit reproduction bottom must become fully visible after scrolling"
        )
        addScreenshot(of: app, named: "Minimal audit reproduction — contrast-only — \(requiredAppearance())")
        try assertAccessibilityAudit(
            in: app,
            scenario: "minimal-audit-repro-contrast-only-post-scroll",
            auditType: .contrast
        )
    }

    private func runOriginalScenarioAudit(scenario: String, expected: String) throws {
        let app = launch(scenario)
        defer { app.terminate() }
        let expectedState = XCTNSPredicateExpectation(
            predicate: NSPredicate { _, _ in
                app.staticTexts[expected].exists
                    || app.buttons[expected].exists
                    || app.progressIndicators[expected].exists
            },
            object: nil
        )
        XCTAssertEqual(XCTWaiter.wait(for: [expectedState], timeout: 5), .completed, "Scenario \(scenario)")
        assertMinimumActionTargets(in: app)
        scrollUntilVisible(app.staticTexts[expected], in: app, field: expected)
        addScreenshot(of: app, named: "Controlled state — \(scenario) — \(requiredAppearance())")
        try assertAccessibilityAudit(in: app, scenario: scenario)
    }

    func testAllControlledScenariosShowExpectedStateAndAudit() throws {
        let states = [
            ("loading", "Loading"), ("emptyRelease", "No current release is available."), ("emptyEngagement", "No current release is available."),
            ("noConclusion", "No conclusion is available."), ("noActions", "No actions are available."), ("denied", "Access denied. Sign in again."),
            ("unavailable", "ACE is unavailable. Try again later."), ("unexpected", "ACE is unavailable. Try again later."),
            ("connection", "ACE could not be reached. Check your connection and try again."), ("timeout", "The request timed out. Try again."),
            ("invalidResponse", "ACE is unavailable. Try again later."), ("secure", "ACE could not establish a secure connection. Try again later."),
            ("keychainRead", "Saved sign-in could not be read. Try again."),
            ("keychainWrite", "Sign-in could not be saved. Try again."), ("keychainDeletion", "Saved sign-in could not be removed. Try again."),
            ("deletionOnly", "Saved sign-in must be reset before access."), ("deletionRetry", "Sign-out could not be completed. Try again."),
            ("copyConfirmation", "Copy Engagement name"), ("privacy", "ACE Client")
        ]
        for (scenario, expected) in states {
            let app = launch(scenario)
            let expectedState = XCTNSPredicateExpectation(
                predicate: NSPredicate { _, _ in
                    app.staticTexts[expected].exists
                        || app.buttons[expected].exists
                        || app.progressIndicators[expected].exists
                },
                object: nil
            )
            XCTAssertEqual(XCTWaiter.wait(for: [expectedState], timeout: 5), .completed, "Scenario \(scenario)")
            assertMinimumActionTargets(in: app)
            addScreenshot(of: app, named: "Controlled state — \(scenario) — \(requiredAppearance())")
            try assertAccessibilityAudit(in: app, scenario: scenario)
            app.terminate()
        }
    }

    func testReleaseOrientationHooks() {
        let app = launch("release")
        XCUIDevice.shared.orientation = .landscapeLeft
        assertOrientation(in: app, landscape: true)
        XCTAssertTrue(app.staticTexts["FICTIONAL PILOT — CONTROLLED"].exists)
        addScreenshot(of: app, named: "Release — landscape-left — \(requiredAppearance())")
        XCUIDevice.shared.orientation = .portrait
        assertOrientation(in: app, landscape: false)
        XCTAssertTrue(app.staticTexts["FICTIONAL PILOT — CONTROLLED"].exists)
        addScreenshot(of: app, named: "Release — portrait — \(requiredAppearance())")
    }

    private func assertOrientation(in app: XCUIApplication, landscape: Bool) {
        let displayedOrientation = XCTNSPredicateExpectation(
            predicate: NSPredicate { _, _ in
                let frame = app.frame
                return landscape ? frame.width > frame.height : frame.height > frame.width
            },
            object: nil
        )
        XCTAssertEqual(
            XCTWaiter.wait(for: [displayedOrientation], timeout: 5),
            .completed,
            "The displayed app must match the requested orientation"
        )
    }

    func testNormalDeviceSettings() throws {
        let expectedAppearance = requiredNormalDeviceAppearance()
        let expectedContentSize = requiredNormalDeviceContentSize()
        XCUIDevice.shared.orientation = .portrait
        let app = launchWithNormalDeviceSettings("release")
        defer { app.terminate() }
        let indicator = app.staticTexts["Effective interface style"]
        XCTAssertTrue(indicator.waitForExistence(timeout: 5), "Appearance indicator must exist")
        let displayedAppearance = XCTNSPredicateExpectation(
            predicate: NSPredicate(format: "label == %@", expectedAppearance), object: indicator
        )
        XCTAssertEqual(
            XCTWaiter.wait(for: [displayedAppearance], timeout: 5),
            .completed,
            "The displayed view must use the simulator's \(expectedAppearance) appearance"
        )
        let displayedContentSize = XCTNSPredicateExpectation(
            predicate: NSPredicate(format: "value == %@", expectedContentSize), object: indicator
        )
        XCTAssertEqual(
            XCTWaiter.wait(for: [displayedContentSize], timeout: 5),
            .completed,
            "The displayed view must use the simulator's \(expectedContentSize) content size"
        )
        assertMinimumActionTargets(in: app)
        try assertAccessibilityAudit(in: app, scenario: "release-normal-device-settings-initial")
        assertFullReleaseInformation(in: app, appearance: "normal-device-settings-\(expectedAppearance)")
        assertMinimumActionTargets(in: app)
        addScreenshot(of: app, named: "Fictional release — normal-device-settings — \(expectedAppearance)")
        try assertAccessibilityAudit(in: app, scenario: "release-normal-device-settings")
    }

    private func assertFullReleaseInformation(in app: XCUIApplication, appearance: String) {
        let values = [
            ("Engagement name", "Fictional Engagement"),
            ("Review status", "RELEASED"),
            ("Release version", "1"),
            ("Published date and time", "2026-08-24T10:15:30Z"),
            ("Conclusion title", "Fictional conclusion"),
            ("Conclusion summary", "Fictional summary"),
            ("Evidence reference", "FICTIONAL-REF-001"),
            ("Action description", "Fictional action"),
            ("Action owner", "Fictional owner"),
            ("Action target date", "2026-08-25"),
            ("Action status", "OPEN")
        ]
        for (field, value) in values {
            let exactLabel = "\(field): \(value)"
            let row = app.descendants(matching: .any)
                .matching(NSPredicate(format: "label == %@", exactLabel))
                .firstMatch
            scrollUntilVisible(row, in: app, field: field)
            assertMinimumActionTargets(in: app)
            addScreenshot(of: app, named: "Release detail — \(field) — \(appearance)", snapshot: XCUIScreen.main.screenshot())
        }
    }

    private func scrollUntilVisible(_ element: XCUIElement, in app: XCUIApplication, field: String) {
        let scrollView = app.scrollViews.firstMatch
        guard scrollView.waitForExistence(timeout: 5) else {
            XCTFail("Release scroll view must exist")
            return
        }
        for _ in 0..<16 {
            if isFullyVisible(element, in: scrollView) { return }
            let scrollViewport = scrollView.frame
            let elementExists = element.exists
            let elementFrame = elementExists ? element.frame : .zero
            let shouldScrollDown = !elementExists || elementFrame == .zero || elementFrame.maxY > scrollViewport.maxY
            drag(scrollView, upward: shouldScrollDown)
        }
        XCTAssertTrue(element.exists, "Missing release value for \(field)")
        XCTAssertTrue(
            isFullyVisible(element, in: scrollView),
            "Release value for \(field) must become fully visible after scrolling"
        )
    }

    private func isFullyVisible(_ element: XCUIElement, in scrollView: XCUIElement) -> Bool {
        guard element.exists && element.isHittable else { return false }
        let elementFrame = element.frame
        let viewport = scrollView.frame
        return elementFrame.width > 0 && elementFrame.height > 0
            && elementFrame.minX >= viewport.minX && elementFrame.maxX <= viewport.maxX
            && elementFrame.minY >= viewport.minY && elementFrame.maxY <= viewport.maxY
    }

    private func drag(_ scrollView: XCUIElement, upward: Bool) {
        let startY: CGFloat = upward ? 0.72 : 0.28
        let endY: CGFloat = upward ? 0.28 : 0.72
        let start = scrollView.coordinate(withNormalizedOffset: CGVector(dx: 0.5, dy: startY))
        let end = scrollView.coordinate(withNormalizedOffset: CGVector(dx: 0.5, dy: endY))
        start.press(forDuration: 0.05, thenDragTo: end)
    }

    private func addScreenshot(
        of app: XCUIApplication,
        named name: String,
        snapshot: XCUIScreenshot? = nil
    ) {
        let screenshot = XCTAttachment(screenshot: snapshot ?? app.screenshot())
        screenshot.name = name
        screenshot.lifetime = .keepAlways
        add(screenshot)
    }

    private func assertMinimumActionTargets(in app: XCUIApplication, file: StaticString = #filePath, line: UInt = #line) {
        // Off-screen elements need scrolling before their hit area can be measured.
        for button in app.buttons.allElementsBoundByIndex where button.isHittable {
            XCTAssertTrue(
                isAtLeast44Points(button.frame.width),
                actionTargetDiagnostic(button.label, dimension: "width", measurement: button.frame.width),
                file: file,
                line: line
            )
            XCTAssertTrue(
                isAtLeast44Points(button.frame.height),
                actionTargetDiagnostic(button.label, dimension: "height", measurement: button.frame.height),
                file: file,
                line: line
            )
        }
    }

    private func isAtLeast44Points(_ measurement: CGFloat) -> Bool {
        let minimum: CGFloat = 44
        // XCTest can report a 44-point SwiftUI target eight ULP below 44.
        return measurement >= minimum || minimum - measurement <= minimum.ulp * 8
    }

    private func actionTargetDiagnostic(_ label: String, dimension: String, measurement: CGFloat) -> String {
        let minimum: CGFloat = 44
        return "\(label) \(dimension): measured \(measurement), minimum \(minimum), tolerance \(minimum.ulp * 8) (eight ULP)"
    }

    private func assertReleaseContrastProbeFramesAreStable(in app: XCUIApplication) {
        let before = releaseContrastProbeFrames(in: app)
        let settleExpectation = XCTestExpectation(description: "Allow the release layout to settle")
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) { settleExpectation.fulfill() }
        XCTAssertEqual(
            XCTWaiter.wait(for: [settleExpectation], timeout: 1),
            .completed,
            "Release layout stability wait must complete"
        )
        let after = releaseContrastProbeFrames(in: app)
        print("ACE_MCX19_CONTRAST_PROBE \(Self.releaseContrastProbeJSON(before: before, after: after))")
        XCTAssertEqual(after.actionHeader, before.actionHeader, "Action 1 frame changed during the release contrast probe")
        XCTAssertEqual(after.actionStatus, before.actionStatus, "OPEN frame changed during the release contrast probe")
    }

    private func releaseContrastProbeFrames(in app: XCUIApplication) -> (actionHeader: CGRect, actionStatus: CGRect) {
        (app.staticTexts["Action 1"].frame, app.staticTexts["OPEN"].frame)
    }

    private static func releaseContrastProbeJSON(
        before: (actionHeader: CGRect, actionStatus: CGRect),
        after: (actionHeader: CGRect, actionStatus: CGRect)
    ) -> String {
        let payload: [String: Any] = [
            "after": ["Action 1": frameJSON(after.actionHeader), "OPEN": frameJSON(after.actionStatus)],
            "before": ["Action 1": frameJSON(before.actionHeader), "OPEN": frameJSON(before.actionStatus)]
        ]
        guard let data = try? JSONSerialization.data(withJSONObject: payload, options: [.sortedKeys]),
              let text = String(data: data, encoding: .utf8) else {
            return "{\"after\":{},\"before\":{}}"
        }
        return text
    }

    private static func frameJSON(_ frame: CGRect) -> [String: Double] {
        ["height": Double(frame.height), "width": Double(frame.width), "x": Double(frame.origin.x), "y": Double(frame.origin.y)]
    }

    private func assertAccessibilityAudit(
        in app: XCUIApplication,
        scenario: String,
        auditType: XCUIAccessibilityAuditType = .all
    ) throws {
        let auditIssueHandler: @Sendable (XCUIAccessibilityAuditIssue) -> Bool = { issue in
            // Keep bounded failure diagnostics for the approved controlled runner.
            print("ACE_A11Y_ISSUE \(Self.accessibilityIssueJSON(issue, scenario: scenario))")
            // Returning false retains XCTest's native audit failure.
            return false
        }
        try app.performAccessibilityAudit(for: auditType, auditIssueHandler)
    }

    private static func accessibilityIssueJSON(_ issue: XCUIAccessibilityAuditIssue, scenario: String) -> String {
        var element: [String: Any] = [
            "identifier": "",
            "label": "",
            "type": "unavailable"
        ]
        if let auditedElement = issue.element {
            element["identifier"] = limitedAuditText(auditedElement.identifier)
            element["label"] = limitedAuditText(auditedElement.label)
            element["type"] = limitedAuditText(String(describing: auditedElement.elementType))
            let frame = auditedElement.frame
            element["frame"] = [
                "height": Double(frame.height),
                "width": Double(frame.width),
                "x": Double(frame.origin.x),
                "y": Double(frame.origin.y)
            ]
        }
        let payload: [String: Any] = [
            "auditType": limitedAuditText(String(describing: issue.auditType)),
            "compactDescription": limitedAuditText(issue.compactDescription),
            "detailedDescription": limitedAuditText(issue.detailedDescription),
            "element": element,
            "scenario": limitedAuditText(scenario)
        ]
        guard let data = try? JSONSerialization.data(withJSONObject: payload, options: [.sortedKeys]),
              let text = String(data: data, encoding: .utf8) else {
            return "{\"auditType\":\"serialization-failed\",\"compactDescription\":\"\",\"detailedDescription\":\"\",\"element\":{\"identifier\":\"\",\"label\":\"\",\"type\":\"unavailable\"},\"scenario\":\"unknown\"}"
        }
        return text
    }

    private static func limitedAuditText(_ value: String) -> String {
        String(value.prefix(256))
    }
}
