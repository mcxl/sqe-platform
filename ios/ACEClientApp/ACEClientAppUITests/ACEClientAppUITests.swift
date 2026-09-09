import Foundation
import CoreGraphics
import XCTest

final class ACEClientAppUITests: XCTestCase {
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
        try assertAccessibilityAudit(in: app, scenario: "release-initial")
        assertFullReleaseInformation(in: app, appearance: requiredAppearance())
        assertMinimumActionTargets(in: app)
        addScreenshot(of: app, named: "Fictional release — approved-controls — \(requiredAppearance())")
        try assertAccessibilityAudit(in: app, scenario: "release")
        app.terminate()

        let confirmationApp = launch("copyConfirmation")
        confirmationApp.buttons["Copy Engagement name"].tap()
        XCTAssertTrue(confirmationApp.staticTexts["Copied Engagement name."].exists, "Copy confirmation must be available to VoiceOver")
        addScreenshot(of: confirmationApp, named: "Controlled state — copyConfirmation — \(requiredAppearance())")
        confirmationApp.terminate()
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
                predicate: NSPredicate { _, _ in app.staticTexts[expected].exists || app.buttons[expected].exists },
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
            addScreenshot(of: app, named: "Release detail — \(field) — \(appearance)")
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

    private func addScreenshot(of app: XCUIApplication, named name: String) {
        let screenshot = XCTAttachment(screenshot: app.screenshot())
        screenshot.name = name
        screenshot.lifetime = .keepAlways
        add(screenshot)
    }

    private func assertMinimumActionTargets(in app: XCUIApplication, file: StaticString = #filePath, line: UInt = #line) {
        // Off-screen elements need scrolling before their hit area can be measured.
        for button in app.buttons.allElementsBoundByIndex where button.isHittable {
            XCTAssertGreaterThanOrEqual(button.frame.width, 44, button.label, file: file, line: line)
            XCTAssertGreaterThanOrEqual(button.frame.height, 44, button.label, file: file, line: line)
        }
    }

    private func assertAccessibilityAudit(in app: XCUIApplication, scenario: String) throws {
        let auditIssueHandler: @Sendable (XCUIAccessibilityAuditIssue) -> Bool = { issue in
            // Keep bounded failure diagnostics for the approved controlled runner.
            print("ACE_A11Y_ISSUE \(Self.accessibilityIssueJSON(issue, scenario: scenario))")
            // Returning false retains XCTest's native audit failure.
            return false
        }
        try app.performAccessibilityAudit(for: .all, auditIssueHandler)
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
