import XCTest

final class ACEClientAppUITests: XCTestCase {
    private func launch(_ scenario: String) -> XCUIApplication {
        let app = XCUIApplication()
        app.launchEnvironment["ACE_UI_TEST_SCENARIO"] = scenario
        if let appearance = ProcessInfo.processInfo.environment["ACE_UI_TEST_APPEARANCE"] {
            app.launchEnvironment["ACE_UI_TEST_APPEARANCE"] = appearance
            app.launchArguments += ["-AppleInterfaceStyle", appearance == "dark" ? "Dark" : "Light"]
        }
        app.launch()
        return app
    }

    func testLaunchShowsSafeConfigurationState() throws {
        let app = launch("configuration")
        XCTAssertTrue(app.staticTexts["This app is not configured for access."].exists)
        try app.performAccessibilityAudit()
    }

    func testSignInPasswordFieldIsSecure() throws {
        let app = launch("signIn")
        XCTAssertTrue(app.secureTextFields["Password"].exists)
        try app.performAccessibilityAudit()
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
        try app.performAccessibilityAudit()
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
            try app.performAccessibilityAudit()
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
}
