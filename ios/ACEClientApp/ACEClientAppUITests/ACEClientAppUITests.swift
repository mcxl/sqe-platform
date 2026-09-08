import Foundation
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

    func testBothAppearances() {
        for appearance in ["light", "dark"] {
            let app = launch("release", appearance: appearance)
            defer { app.terminate() }
            let indicator = app.staticTexts["Effective interface style"]
            XCTAssertTrue(indicator.waitForExistence(timeout: 5), "Appearance indicator must exist")
            let displayedAppearance = XCTNSPredicateExpectation(
                predicate: NSPredicate(format: "label == %@", appearance), object: indicator
            )
            XCTAssertEqual(XCTWaiter.wait(for: [displayedAppearance], timeout: 5), .completed,
                           "The displayed view must use \(appearance) appearance")
            XCTAssertTrue(app.staticTexts["FICTIONAL PILOT — CONTROLLED"].exists)
            let screenshot = XCTAttachment(screenshot: app.screenshot())
            screenshot.name = "Fictional release — \(appearance)"
            screenshot.lifetime = .keepAlways
            add(screenshot)
        }
    }

    func testLaunchShowsSafeConfigurationState() throws {
        let app = launch("configuration")
        XCTAssertTrue(app.staticTexts["This app is not configured for access."].exists)
        try assertAccessibilityAudit(in: app, scenario: "configuration")
    }

    func testSignInPasswordFieldIsSecure() throws {
        let app = launch("signIn")
        XCTAssertTrue(app.secureTextFields["Password"].exists)
        assertMinimumActionTargets(in: app)
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
        try assertAccessibilityAudit(in: app, scenario: "release")
        app.terminate()

        let confirmationApp = launch("copyConfirmation")
        confirmationApp.buttons["Copy Engagement name"].tap()
        XCTAssertTrue(confirmationApp.staticTexts["Copied Engagement name."].exists, "Copy confirmation must be available to VoiceOver")
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
            try assertAccessibilityAudit(in: app, scenario: scenario)
            app.terminate()
        }
    }

    func testReleaseOrientationHooks() {
        let app = launch("release")
        XCUIDevice.shared.orientation = .landscapeLeft
        XCTAssertTrue(app.staticTexts["FICTIONAL PILOT — CONTROLLED"].exists)
        XCUIDevice.shared.orientation = .portrait
        XCTAssertTrue(app.staticTexts["FICTIONAL PILOT — CONTROLLED"].exists)
    }

    private func assertMinimumActionTargets(in app: XCUIApplication, file: StaticString = #filePath, line: UInt = #line) {
        // Off-screen elements need scrolling before their hit area can be measured.
        for button in app.buttons.allElementsBoundByIndex where button.isHittable {
            XCTAssertGreaterThanOrEqual(button.frame.width, 44, button.label, file: file, line: line)
            XCTAssertGreaterThanOrEqual(button.frame.height, 44, button.label, file: file, line: line)
        }
    }

    private func assertAccessibilityAudit(in app: XCUIApplication, scenario: String) throws {
        try app.performAccessibilityAudit(for: .all) { issue in
            // Keep bounded failure diagnostics for the approved controlled runner.
            print("ACE_A11Y_ISSUE \(accessibilityIssueJSON(issue, scenario: scenario))")
            // Returning false retains XCTest's native audit failure.
            return false
        }
    }

    private func accessibilityIssueJSON(_ issue: XCUIAccessibilityAuditIssue, scenario: String) -> String {
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

    private func limitedAuditText(_ value: String) -> String {
        String(value.prefix(256))
    }
}
