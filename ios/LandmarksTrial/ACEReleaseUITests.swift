import XCTest
import UIKit

final class LandmarksTrialUITests: XCTestCase {
    override func setUpWithError() throws {
        continueAfterFailure = false
    }

    @MainActor
    func testReleaseInformationAndCopyControls() throws {
        let app = XCUIApplication()
        app.launch()

        setOrientation(.portrait, in: app, name: "release-portrait")
        let fields = releaseFields
        roundTripToCurrentRelease(in: app)
        for (label, value) in fields {
            let valueElement = app.descendants(matching: .any)
                .matching(NSPredicate(format: "label == %@", "\(label): \(value)")).firstMatch
            scrollToElement(valueElement, in: app)
            require(valueElement.exists && valueElement.isHittable, in: app, name: "copy-\(label)-value", "Missing \(label): \(value)")
            let copyButton = app.buttons["Copy \(label)"]
            scrollToElement(copyButton, in: app)
            require(copyButton.exists && copyButton.isHittable, in: app, name: "copy-\(label)-control", "Missing copy control for \(label)")
            copyButton.tap()
            let actual = UIPasteboard.general.string
            requireEqual(actual, value, in: app, name: "copy-\(label)-payload", "Copy payload mismatch for \(label): expected \(value); actual \(actual ?? "nil")")
            let confirmation = app.staticTexts["Copied \(label)."]
            require(confirmation.waitForExistence(timeout: 2), in: app, name: "copy-\(label)-confirmation", "Missing copied confirmation for \(label)")
        }
        attachScreenshot(app, name: "release-portrait-success")
        try audit(app, name: "release-portrait")
        launchLandscape(app, name: "release-landscape")
        assertValues(fields, in: app, scenario: "release-landscape")
        attachScreenshot(app, name: "release-landscape-success")
        try audit(app, name: "release-landscape")
    }

    @MainActor
    func testReleaseLayoutAndAccessibility() throws {
        let app = XCUIApplication()
        app.launch()

        setOrientation(.portrait, in: app, name: "accessibility-portrait")
        try auditVisiblePages(releaseFields, in: app, scenario: "accessibility-portrait")
        launchLandscape(app, name: "accessibility-landscape")
        try auditVisiblePages(releaseFields, in: app, scenario: "accessibility-landscape")
    }

    @MainActor
    private func setOrientation(_ orientation: UIDeviceOrientation, in app: XCUIApplication, name: String) {
        XCUIDevice.shared.orientation = orientation
        require(app.navigationBars["Release Details"].waitForExistence(timeout: 10), in: app, name: "\(name)-launch", "Release detail did not load for \(name)")
        let frame = app.windows.firstMatch.frame
        let expected = orientation.isLandscape ? "width > height" : "width < height"
        let actual = "width=\(frame.width); height=\(frame.height)"
        let isExpectedAspect = orientation.isLandscape ? frame.width > frame.height : frame.width < frame.height
        require(isExpectedAspect, in: app, name: "\(name)-aspect", "Unexpected app window aspect for \(name): expected \(expected); actual \(actual)")
    }

    @MainActor
    private func launchLandscape(_ app: XCUIApplication, name: String) {
        XCUIDevice.shared.orientation = .landscapeLeft
        app.terminate()
        app.launch()
        setOrientation(.landscapeLeft, in: app, name: name)
    }

    @MainActor
    private func audit(_ app: XCUIApplication, name: String) throws {
        attachScreenshot(app, name: name)
        let diagnostic = XCTAttachment(string: "orientation=\(XCUIDevice.shared.orientation.rawValue); frame=\(app.windows.firstMatch.frame)")
        diagnostic.name = "\(name)-traits"
        diagnostic.lifetime = .keepAlways
        add(diagnostic)
        do {
            try app.performAccessibilityAudit(for: .all)
        } catch {
            attachFailureEvidence(app, name: "\(name)-audit-failure")
            throw error
        }
    }

    @MainActor
    private func scrollToElement(_ element: XCUIElement, in app: XCUIApplication) {
        for _ in 0..<12 where !element.exists || !element.isHittable {
            app.swipeUp()
        }
    }

    @MainActor
    private func assertValues(_ fields: [(String, String)], in app: XCUIApplication, scenario: String) {
        for (label, value) in fields {
            let valueElement = app.descendants(matching: .any)
                .matching(NSPredicate(format: "label == %@", "\(label): \(value)")).firstMatch
            scrollToElement(valueElement, in: app)
            require(valueElement.exists && valueElement.isHittable, in: app, name: "\(scenario)-\(label)", "Missing \(label): \(value)")
        }
    }

    @MainActor
    private func auditVisiblePages(_ fields: [(String, String)], in app: XCUIApplication, scenario: String) throws {
        for (label, value) in fields {
            let valueElement = app.descendants(matching: .any)
                .matching(NSPredicate(format: "label == %@", "\(label): \(value)")).firstMatch
            scrollToElement(valueElement, in: app)
            require(valueElement.exists && valueElement.isHittable, in: app, name: "\(scenario)-\(label)", "Missing \(label): \(value)")
            try audit(app, name: "\(scenario)-\(label)")
        }
    }

    @MainActor
    private func attachFailureEvidence(_ app: XCUIApplication, name: String) {
        attachScreenshot(app, name: name)
        let hierarchy = XCTAttachment(string: app.debugDescription)
        hierarchy.name = "\(name)-hierarchy"
        hierarchy.lifetime = .keepAlways
        add(hierarchy)
    }

    @MainActor
    private func roundTripToCurrentRelease(in app: XCUIApplication) {
        let navigationButtons = app.navigationBars.buttons
        let sidebarButton = navigationButtons["Show Sidebar"].firstMatch
        let navigationButton = sidebarButton.exists ? sidebarButton : navigationButtons.firstMatch
        require(navigationButton.exists && navigationButton.isHittable, in: app, name: "release-sidebar-control", "The sidebar navigation control was unavailable")
        navigationButton.tap()
        let currentRelease = app.staticTexts["Current Release"].firstMatch
        require(currentRelease.waitForExistence(timeout: 10), in: app, name: "release-sidebar-row", "Current Release was unavailable in the sidebar")
        currentRelease.tap()
        require(app.navigationBars["Release Details"].waitForExistence(timeout: 10), in: app, name: "release-detail-return", "Release Details did not return from the sidebar")
    }

    @MainActor
    private func attachScreenshot(_ app: XCUIApplication, name: String) {
        let screenshot = XCTAttachment(screenshot: app.screenshot())
        screenshot.name = name
        screenshot.lifetime = .keepAlways
        add(screenshot)
    }

    @MainActor
    private func require(_ condition: @autoclosure () -> Bool, in app: XCUIApplication, name: String, _ message: String) {
        guard condition() else {
            attachFailureEvidence(app, name: name)
            XCTFail(message)
            return
        }
    }

    @MainActor
    private func requireEqual(_ actual: String?, _ expected: String, in app: XCUIApplication, name: String, _ message: String) {
        guard actual == expected else {
            attachFailureEvidence(app, name: name)
            XCTFail(message)
            return
        }
    }

    private let releaseFields = [
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
}
