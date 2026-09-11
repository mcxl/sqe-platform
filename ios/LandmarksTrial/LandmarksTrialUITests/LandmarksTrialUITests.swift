import XCTest

final class LandmarksTrialUITests: XCTestCase {
    @MainActor
    func testLaunchShowsFeaturedMountFuji() {
        let app = XCUIApplication()
        app.launch()

        let expected = true
        let actual = app.staticTexts["Mount Fuji"].firstMatch.waitForExistence(timeout: 10)
        let attachment = XCTAttachment(screenshot: app.screenshot())
        attachment.name = "landmarks-launch"
        attachment.lifetime = .keepAlways
        add(attachment)

        XCTAssertEqual(actual, expected, "Expected Mount Fuji to exist: \(expected); actual: \(actual)")
    }
}
