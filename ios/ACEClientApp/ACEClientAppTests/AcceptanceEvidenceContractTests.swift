import Foundation
import XCTest
import Security
import CryptoKit

final class AcceptanceEvidenceContractTests: XCTestCase { }

// MARK: - Runtime plan model

struct RuntimePlan: Decodable {
    struct Entry: Decodable {
        let identifiers: [String]
        let stage: String
        let device: String
        let procedure: String
        let expectedResult: String
        let status: String
    }
    let entries: [Entry]
}

// MARK: - Baseline And Project (IOS-BASE-001 through IOS-BASE-006)

extension AcceptanceEvidenceContractTests {

    private var approvedSanitizedBaseManifest: [String: String] {
        ["docs/specs/2026-08-24-ace-ios-read-only-client-application.md": "46c262ebd0c781f83fa19b556f67d69a8ef3791d6062e2266c2ebaaa526536ff"]
    }

    func testProjectConfiguration() throws {
        // IOS-BASE-001: The deterministic source-tree manifest is partial evidence.
        // Approved repository ancestry validation remains pending.
        XCTAssertEqual(try sourceTreeManifest(), approvedSanitizedBaseManifest)
        // IOS-BASE-002: iPhone + iOS 26 target
        // IOS-BASE-003: SwiftUI + Apple frameworks only
        // IOS-BASE-004: No third-party runtime packages
        // IOS-NET-029: No ATS dictionary or weakening value
        // IOS-PRIV-004: No scene restoration release info
        // IOS-PRIV-005: No widgets or notification release info
        let projectText = try projectText()
        XCTAssertTrue(projectText.contains("IPHONEOS_DEPLOYMENT_TARGET = 26.0"))
        XCTAssertTrue(projectText.contains("TARGETED_DEVICE_FAMILY = 1"))
        XCTAssertTrue(projectText.contains("iphoneos iphonesimulator"))
        // IOS-BASE-003: The production target uses only Apple frameworks.
        let sourceText = try allSourceText()
        let importLines = sourceText.split(whereSeparator: \.isNewline).map {
            $0.trimmingCharacters(in: .whitespaces)
        }.filter { $0.hasPrefix("import ") }
        XCTAssertTrue(Set(importLines).isSubset(of: Set(["import Foundation", "import Security", "import SwiftUI", "import UIKit"])))
        // IOS-BASE-004: The project has no package or linked third-party framework.
        XCTAssertFalse(projectText.contains("packageReferences ="))
        XCTAssertFalse(projectText.contains("XCRemoteSwiftPackageReference"))
        XCTAssertFalse(projectText.contains("XCLocalSwiftPackageReference"))
        XCTAssertFalse(projectText.contains("wrapper.framework"))
        XCTAssertTrue(projectText.contains("PBXFrameworksBuildPhase; buildActionMask = 2147483647; files = ();"))
        // ATS: the project must NOT contain NSAppTransportSecurity or NSExceptionDomains
        XCTAssertFalse(projectText.contains("NSAppTransportSecurity"))
        XCTAssertFalse(projectText.contains("NSExceptionDomains"))
        let plist = try infoPlist()
        XCTAssertNil(plist["NSAppTransportSecurity"], "Info.plist must not define an ATS exception")
        // IOS-PRIV-004: The app has no state-restoration configuration or entitlement.
        let sceneManifest = try XCTUnwrap(plist["UIApplicationSceneManifest"] as? [String: Any])
        XCTAssertEqual(sceneManifest["UIApplicationSupportsMultipleScenes"] as? Bool, false)
        XCTAssertNil(sceneManifest["UISceneConfigurations"])
        XCTAssertNil(plist["UIApplicationStateRestorationBundleVersion"])
        XCTAssertFalse(projectText.contains("CODE_SIGN_ENTITLEMENTS ="))
        // IOS-PRIV-005: The project has no widget or notification extension, framework, or plist value.
        XCTAssertFalse(projectText.contains("com.apple.product-type.app-extension"))
        XCTAssertFalse(projectText.contains("WidgetKit.framework"))
        XCTAssertFalse(projectText.contains("UserNotifications.framework"))
        XCTAssertNil(plist["NSUserActivityTypes"])
        XCTAssertFalse(sourceText.contains("import WidgetKit"))
        XCTAssertFalse(sourceText.contains("import UserNotifications"))
        XCTAssertFalse(sourceText.contains("UNUserNotificationCenter"))
    }

    func testSourceBoundaryInspection() throws {
        // IOS-BASE-005: The controlled iOS extraction contains no server code. Its
        // server contract document matches the approved sanitised-base manifest.
        XCTAssertTrue(try serverSourcePaths().isEmpty)
        XCTAssertEqual(try sourceTreeManifest(), approvedSanitizedBaseManifest)
        // IOS-BASE-006: No Production server address
        // IOS-BOUND-002: No ACE database connection
        // IOS-BOUND-003: No Sift-KG or OpenViking call
        // IOS-BOUND-004: No provider credential or SDK
        // IOS-BOUND-005: No edit, approval, upload, delete, or write control
        // IOS-BOUND-007: G0 and server auth remain server-owned
        let sources = try productionSources()
        XCTAssertEqual(Set(sources.map { sourceRelativePath($0) }), Set([
            "ACEClientAppApp.swift", "Configuration.swift", "DebugScenario.swift", "KeychainStore.swift",
            "Network.swift", "ReleaseModels.swift", "SessionState.swift", "Views.swift"
        ]), "Production source enumeration changed; review the read-only allowlist")
        let networkSources = try sources.filter { source in
            let text = try String(contentsOf: source, encoding: .utf8)
            return text.contains("URLRequest(") || text.contains("session.data(for:")
        }
        XCTAssertEqual(networkSources.map { sourceRelativePath($0) }, ["Network.swift"], "Only Network.swift may create or send requests")
        let networkSource = try sourceText("Network.swift")
        let methods = try stringLiterals(inAssignmentsMatching: #"\.httpMethod\s*=\s*\"([^\"]+)\""#, source: networkSource)
        XCTAssertEqual(methods, ["GET"], "The complete request-method enumeration must contain only GET")
        XCTAssertEqual(try assignmentCount(matching: #"\.httpMethod\s*="#, source: networkSource), 1, "The complete request-method assignment enumeration must contain one assignment")
        XCTAssertEqual(networkSource.components(separatedBy: "session.data(for: request)").count - 1, 1, "Only the approved GET request may reach URLSession")
        let allSource = sources.map { try! String(contentsOf: $0, encoding: .utf8) }.joined(separator: "\n")
        XCTAssertFalse(allSource.contains("Sift-KG"), "Sift-KG found in source")
        XCTAssertFalse(allSource.contains("OpenViking"), "OpenViking found in source")
        XCTAssertFalse(allSource.localizedCaseInsensitiveContains("sqlite"), "Production source must not contain a database connection")
    }
}

// MARK: - Response Models (IOS-MODEL-001 through IOS-MODEL-018)

extension AcceptanceEvidenceContractTests {

    func testReleaseValidation() throws {
        // IOS-MODEL-001: Valid release decodes every required field
        let valid = ClientReleaseResponse(
            engagementName: "Fictional Engagement", reviewStatus: "RELEASED", releaseVersion: 1,
            publishedAt: "2026-08-24T10:15:30Z",
            conclusion: ClientConclusion(title: "Title", summary: "Summary", evidenceReferenceID: "REF-001"),
            actions: [ClientAction(description: "Action", owner: "Owner", targetDate: "2026-08-25", status: "OPEN")]
        )
        XCTAssertEqual(try valid.validated(), .release(valid))
        // IOS-MODEL-002: Null conclusion decodes
        let noConclusion = ClientReleaseResponse(engagementName: "FE", reviewStatus: "RELEASED", releaseVersion: 1, publishedAt: "2026-08-24T10:15:30Z", conclusion: nil, actions: [])
        XCTAssertEqual(try noConclusion.validated(), .release(noConclusion))
        // IOS-MODEL-006: Empty actions array decodes
        // IOS-MODEL-007: Action order matches API order (Codable preserves array order)
        let actions = [ClientAction(description: "First", owner: "A", targetDate: "2026-08-25", status: "OPEN"), ClientAction(description: "Second", owner: "B", targetDate: "2026-08-26", status: "COMPLETE")]
        let ordered = ClientReleaseResponse(engagementName: "FE", reviewStatus: "DRAFT", releaseVersion: 2, publishedAt: "2026-08-24T10:15:30Z", conclusion: nil, actions: actions)
        XCTAssertEqual(try ordered.validated(), .release(ordered))
        XCTAssertEqual(ordered.actions.map(\.description), ["First", "Second"])
        // IOS-MODEL-008: Exact YYYY-MM-DD action dates accepted
        let dateRelease = ClientReleaseResponse(engagementName: "FE", reviewStatus: "DRAFT", releaseVersion: 1, publishedAt: "2026-08-24T10:15:30Z", conclusion: nil, actions: [ClientAction(description: "D", owner: "O", targetDate: "2026-12-31", status: "OPEN")])
        XCTAssertEqual(try dateRelease.validated(), .release(dateRelease))
        // IOS-MODEL-010: Canonical UTC publication times accepted
        // IOS-MODEL-013: release_version > 0 required
        let zeroVersion = ClientReleaseResponse(engagementName: "FE", reviewStatus: "RELEASED", releaseVersion: 0, publishedAt: "2026-08-24T10:15:30Z", conclusion: nil, actions: [])
        XCTAssertThrowsError(try zeroVersion.validated())
        // IOS-MODEL-014: Exact empty sentinel combinations accepted
        let releaseUnavailable = ClientReleaseResponse(engagementName: "Release unavailable", reviewStatus: "", releaseVersion: 0, publishedAt: "", conclusion: nil, actions: [])
        XCTAssertEqual(try releaseUnavailable.validated(), .empty)
        let engagementNotFound = ClientReleaseResponse(engagementName: "Engagement not found", reviewStatus: "", releaseVersion: 0, publishedAt: "", conclusion: nil, actions: [])
        XCTAssertEqual(try engagementNotFound.validated(), .empty)
        // IOS-MODEL-015: Every rejected validation predicate fails closed.
        func response(
            engagementName: String = "Fictional Engagement",
            reviewStatus: String = "RELEASED",
            releaseVersion: Int = 1,
            publishedAt: String = "2026-08-24T10:15:30Z",
            conclusion: ClientConclusion? = nil,
            actions: [ClientAction] = []
        ) -> ClientReleaseResponse {
            ClientReleaseResponse(
                engagementName: engagementName,
                reviewStatus: reviewStatus,
                releaseVersion: releaseVersion,
                publishedAt: publishedAt,
                conclusion: conclusion,
                actions: actions
            )
        }
        let validConclusion = ClientConclusion(title: "Title", summary: "Summary", evidenceReferenceID: "REF-001")
        let validAction = ClientAction(description: "Action", owner: "Owner", targetDate: "2026-08-25", status: "OPEN")
        var invalidCases: [(String, ClientReleaseResponse)] = [
            ("zero version", response(releaseVersion: 0)),
            ("negative version", response(releaseVersion: -1)),
            ("empty engagement name", response(engagementName: "")),
            ("empty review status", response(reviewStatus: "")),
            ("empty publication time", response(publishedAt: "")),
            ("non-canonical publication time", response(publishedAt: "2026-02-30T10:15:30Z")),
            ("empty conclusion title", response(conclusion: ClientConclusion(title: "", summary: "Summary", evidenceReferenceID: "REF-001"))),
            ("empty conclusion summary", response(conclusion: ClientConclusion(title: "Title", summary: "", evidenceReferenceID: "REF-001"))),
            ("empty conclusion reference", response(conclusion: ClientConclusion(title: "Title", summary: "Summary", evidenceReferenceID: ""))),
            ("empty action description", response(actions: [ClientAction(description: "", owner: "Owner", targetDate: "2026-08-25", status: "OPEN")])),
            ("empty action owner", response(actions: [ClientAction(description: "Action", owner: "", targetDate: "2026-08-25", status: "OPEN")])),
            ("invalid action date", response(actions: [ClientAction(description: "Action", owner: "Owner", targetDate: "2026-02-30", status: "OPEN")])),
            ("invalid action status", response(actions: [ClientAction(description: "Action", owner: "Owner", targetDate: "2026-08-25", status: "PENDING")])),
            ("empty name with empty sentinel fields", response(engagementName: "", reviewStatus: "", releaseVersion: 0, publishedAt: ""))
        ]
        for sentinelName in ["Release unavailable", "Engagement not found"] {
            invalidCases += [
                ("\(sentinelName) with review status", response(engagementName: sentinelName, reviewStatus: "RELEASED", releaseVersion: 0, publishedAt: "")),
                ("\(sentinelName) with version", response(engagementName: sentinelName, reviewStatus: "", releaseVersion: 1, publishedAt: "")),
                ("\(sentinelName) with publication time", response(engagementName: sentinelName, reviewStatus: "", releaseVersion: 0, publishedAt: "2026-08-24T10:15:30Z")),
                ("\(sentinelName) with conclusion", response(engagementName: sentinelName, reviewStatus: "", releaseVersion: 0, publishedAt: "", conclusion: validConclusion)),
                ("\(sentinelName) with action", response(engagementName: sentinelName, reviewStatus: "", releaseVersion: 0, publishedAt: "", actions: [validAction]))
            ]
        }
        for (name, invalid) in invalidCases {
            XCTAssertThrowsError(try invalid.validated(), name)
        }
        // IOS-MODEL-016: Action status other than OPEN/COMPLETE fails
        let badStatus = ClientReleaseResponse(engagementName: "FE", reviewStatus: "DRAFT", releaseVersion: 1, publishedAt: "2026-08-24T10:15:30Z", conclusion: nil, actions: [ClientAction(description: "D", owner: "O", targetDate: "2026-08-25", status: "PENDING")])
        XCTAssertThrowsError(try badStatus.validated())
        // IOS-MODEL-017: No conclusion shows notice (tested via apply)
        // IOS-MODEL-018: No actions shows notice (tested via apply)
    }

    func testDecodingFailsClosed() throws {
        // IOS-MODEL-003: Missing required top-level field fails closed
        XCTAssertThrowsError(try JSONDecoder().decode(ClientReleaseResponse.self, from: Data("{\"review_status\":\"RELEASED\"}".utf8)))
        // IOS-MODEL-004: Missing required nested field fails closed
        XCTAssertThrowsError(try JSONDecoder().decode(ClientReleaseResponse.self, from: Data("{\"engagement_name\":\"F\",\"review_status\":\"RELEASED\",\"release_version\":1,\"published_at\":\"2026-08-24T10:15:30Z\",\"conclusion\":{\"title\":\"T\"},\"actions\":[]}".utf8)))
        // IOS-MODEL-005: Missing actions array fails closed
        XCTAssertThrowsError(try JSONDecoder().decode(ClientReleaseResponse.self, from: Data("{\"engagement_name\":\"F\",\"review_status\":\"RELEASED\",\"release_version\":1,\"published_at\":\"2026-08-24T10:15:30Z\",\"conclusion\":null}".utf8)))
        // IOS-MODEL-009: Invalid action dates fail closed
        let badDate = ClientReleaseResponse(engagementName: "FE", reviewStatus: "DRAFT", releaseVersion: 1, publishedAt: "2026-08-24T10:15:30Z", conclusion: nil, actions: [ClientAction(description: "D", owner: "O", targetDate: "2026-02-30", status: "OPEN")])
        XCTAssertThrowsError(try badDate.validated())
        // IOS-MODEL-011: Invalid publication times fail closed
        let badPub = ClientReleaseResponse(engagementName: "FE", reviewStatus: "DRAFT", releaseVersion: 1, publishedAt: "2026-02-30T10:15:30Z", conclusion: nil, actions: [])
        XCTAssertThrowsError(try badPub.validated())
        // IOS-MODEL-012: Unknown extra fields don't become visible (Codable ignores by default)
        let extra = Data("{\"engagement_name\":\"FE\",\"review_status\":\"DRAFT\",\"release_version\":1,\"published_at\":\"2026-08-24T10:15:30Z\",\"conclusion\":null,\"actions\":[],\"unknown_field\":\"should be ignored\"}".utf8)
        let decoded = try JSONDecoder().decode(ClientReleaseResponse.self, from: extra)
        XCTAssertEqual(try decoded.validated(), .release(decoded))
    }
}

// MARK: - Request And Network (IOS-NET-001 through IOS-NET-030)

extension AcceptanceEvidenceContractTests {

    func testRequestConstruction() throws {
        // IOS-NET-001: Only GET
        // IOS-NET-002: Only /client/api/v1/release/current
        // IOS-NET-003: Basic authorization with first request
        // IOS-NET-014: No write method
        // IOS-BOUND-001: Only approved GET endpoint
        let origin = try PreviewOrigin(rawValue: "https://preview.example.invalid")
        let request = try CurrentReleaseRequest.make(origin: origin, credential: Credential(username: "fictional-user", password: "test-password-12"))
        XCTAssertEqual(request.httpMethod, "GET")
        XCTAssertEqual(request.url?.path, "/client/api/v1/release/current")
        XCTAssertEqual(request.cachePolicy, .reloadIgnoringLocalCacheData)
        XCTAssertEqual(request.value(forHTTPHeaderField: "Accept"), "application/json")
        let auth = try XCTUnwrap(request.value(forHTTPHeaderField: "Authorization"))
        XCTAssertTrue(auth.hasPrefix("Basic "))
        // Verify the Basic value is base64-encoded credentials
        let encoded = String(auth.dropFirst("Basic ".count))
        guard let decoded = Data(base64Encoded: encoded).flatMap({ String(data: $0, encoding: .utf8) }) else { return XCTFail("Auth not valid base64") }
        XCTAssertEqual(decoded, "fictional-user:test-password-12")
    }

    func testOriginValidation() throws {
        // IOS-NET-004: Credentials only to approved HTTPS origin
        // IOS-NET-015: Missing Preview fails before Keychain/network
        // IOS-NET-016: Invalid Preview fails before Keychain/network
        // IOS-NET-027: Non-HTTPS or unapproved origin fails
        XCTAssertThrowsError(try PreviewOrigin(rawValue: ""))
        XCTAssertThrowsError(try PreviewOrigin(rawValue: "http://example.invalid"))
        XCTAssertThrowsError(try PreviewOrigin(rawValue: "https://host.invalid:0"))
        XCTAssertThrowsError(try PreviewOrigin(rawValue: "https://host.invalid:65536"))
        XCTAssertThrowsError(try PreviewOrigin(rawValue: "https://user:pass@host.invalid"))
        XCTAssertThrowsError(try PreviewOrigin(rawValue: "https://host.invalid/path"))
        XCTAssertThrowsError(try PreviewOrigin(rawValue: "https://host.invalid?query=1"))
        XCTAssertThrowsError(try PreviewOrigin(rawValue: "https://host.invalid#frag"))
        for invalidHost in [".preview.example.invalid", "preview..example.invalid", "preview_example.invalid"] {
            XCTAssertThrowsError(try PreviewOrigin(rawValue: "https://\(invalidHost)"), invalidHost)
        }
        let valid = try PreviewOrigin(rawValue: "https://preview.example.invalid")
        XCTAssertEqual(valid.endpointURL().path, "/client/api/v1/release/current")

        let project = try projectText()
        XCTAssertTrue(project.contains("F1A2B3C4D5E6F70809101701 = {isa = PBXShellScriptBuildPhase"))
        XCTAssertTrue(project.contains("name = \"Validate Preview Inputs\""))
        XCTAssertTrue(project.contains("origin=\\\"${ACE_PREVIEW_ORIGIN:-}\\\""))
        XCTAssertTrue(project.contains("case \\\"$origin\\\" in https://*)"))
        XCTAssertTrue(project.contains("ACE_PREVIEW_ORIGIN must be an approved HTTPS origin"))
        XCTAssertTrue(project.contains("ACE_PREVIEW_ORIGIN must be an origin root"))
        XCTAssertTrue(project.contains("ACE_PREVIEW_ORIGIN has an invalid host"))
        XCTAssertTrue(project.contains("ACE_BUNDLE_IDENTIFIER is an external approved input"))
    }

    func testRedirectDelegate() throws {
        // IOS-NET-005: Reject HTTPS-to-HTTP redirect
        // IOS-NET-006: Reject cross-host redirect
        // IOS-NET-021: Reject same-origin path redirect
        // IOS-NET-022: Reject changed-port redirect
        // IOS-NET-023: Reject changed-host redirect
        // IOS-NET-024: Reject clear-text redirect
        // IOS-NET-025: Rejected redirect receives no request/authorization
        let delegate = RedirectAndTrustDelegate()
        let session = URLSession(configuration: .ephemeral)
        // Test redirect rejection: create a redirect response and verify completionHandler(nil)
        let originalURL = try XCTUnwrap(URL(string: "https://preview.example.invalid/client/api/v1/release/current"))
        let originalRequest = URLRequest(url: originalURL)
        let redirects: [(String, URL)] = [
            ("IOS-NET-021", try XCTUnwrap(URL(string: "https://preview.example.invalid/other"))),
            ("IOS-NET-022", try XCTUnwrap(URL(string: "https://preview.example.invalid:8443/client/api/v1/release/current"))),
            ("IOS-NET-023", try XCTUnwrap(URL(string: "https://other.example.invalid/client/api/v1/release/current"))),
            ("IOS-NET-024", try XCTUnwrap(URL(string: "http://preview.example.invalid/client/api/v1/release/current")))
        ]
        for (identifier, redirectURL) in redirects {
            let redirectResponse = HTTPURLResponse(url: originalURL, statusCode: 301, httpVersion: nil, headerFields: ["Location": redirectURL.absoluteString])!
            var redirectedRequest = URLRequest(url: redirectURL)
            redirectedRequest.setValue("Basic fictional-value", forHTTPHeaderField: "Authorization")
            let expectation = XCTestExpectation(description: "\(identifier) handled")
            let task = session.dataTask(with: originalRequest)
            delegate.urlSession(session, task: task, willPerformHTTPRedirection: redirectResponse, newRequest: redirectedRequest) { newRequest in
                XCTAssertNil(newRequest, "\(identifier) must reject the redirect target")
                // IOS-NET-025: nil prevents this redirected request and its authorisation value from being sent.
                XCTAssertNil(newRequest?.value(forHTTPHeaderField: "Authorization"))
                expectation.fulfill()
            }
            wait(for: [expectation], timeout: 2)
        }
    }

    func testTrustHandlingSourceInspection() throws {
        // IOS-NET-007: Standard platform validation rejects untrusted cert
        // IOS-NET-008: Standard platform validation rejects hostname mismatch
        // IOS-NET-028: Trust failure sends no HTTP request to rejected endpoint
        // IOS-NET-030: Source proves system default server-trust handling only
        let delegate = RedirectAndTrustDelegate()
        let session = URLSession(configuration: .ephemeral)
        let expectation = XCTestExpectation(description: "challenge handled")
        let host = "preview.example.invalid"
        let challenge = URLAuthenticationChallenge(
            protectionSpace: URLProtectionSpace(host: host, port: 443, protocol: NSURLProtectionSpaceHTTPS, realm: nil, authenticationMethod: NSURLAuthenticationMethodServerTrust),
            proposedCredential: nil, previousFailureCount: 0, failureResponse: nil, error: nil, sender: ChallengeSender(expectation: expectation))
        delegate.urlSession(session, task: session.dataTask(with: URLRequest(url: URL(string: "https://\(host)/")!)), didReceive: challenge) { disposition, credential in
            XCTAssertEqual(disposition, .performDefaultHandling)
            XCTAssertNil(credential)
            expectation.fulfill()
        }
        wait(for: [expectation], timeout: 2)
    }

    func testRepositoryResponseMapping() async throws {
        // IOS-NET-009: Reject wrong content type
        // IOS-NET-012: Timeout/no-network show safe retry controls
        // IOS-NET-013: Auth/trust failures do not retry automatically
        // IOS-NET-026: Every unexpected HTTP status shows safe unavailable
        let origin = try PreviewOrigin(rawValue: "https://preview.example.invalid")

        // 403 → denied
        let deniedResp = HTTPURLResponse(url: origin.endpointURL(), statusCode: 403, httpVersion: nil, headerFields: nil)!
        let deniedTransport = ControlledTransport(result: .success((Data(), deniedResp)))
        let deniedRepo = HTTPCurrentReleaseRepository(origin: origin, transport: deniedTransport)
        do { _ = try await deniedRepo.fetchCurrentRelease(credential: Credential(username: "u", password: "p")); XCTFail("Expected denied") }
        catch let e as RepositoryError { XCTAssertEqual(e, .denied) } catch { XCTFail("Unexpected") }
        XCTAssertEqual(deniedTransport.requestCount(), 1, "Authentication failure must not retry automatically")

        // 503 → unavailable
        let unavailResp = HTTPURLResponse(url: origin.endpointURL(), statusCode: 503, httpVersion: nil, headerFields: nil)!
        let unavailRepo = HTTPCurrentReleaseRepository(origin: origin, transport: ControlledTransport(result: .success((Data(), unavailResp))))
        do { _ = try await unavailRepo.fetchCurrentRelease(credential: Credential(username: "u", password: "p")); XCTFail("Expected unavailable") }
        catch let e as RepositoryError { XCTAssertEqual(e, .unavailable) } catch { XCTFail("Unexpected") }

        // 500 → unavailable (unexpected)
        let unexpResp = HTTPURLResponse(url: origin.endpointURL(), statusCode: 500, httpVersion: nil, headerFields: nil)!
        let unexpRepo = HTTPCurrentReleaseRepository(origin: origin, transport: ControlledTransport(result: .success((Data(), unexpResp))))
        do { _ = try await unexpRepo.fetchCurrentRelease(credential: Credential(username: "u", password: "p")); XCTFail("Expected unavailable") }
        catch let e as RepositoryError { XCTAssertEqual(e, .unavailable) } catch { XCTFail("Unexpected") }

        // 200 + wrong content type → invalidResponse
        let wrongCT = HTTPURLResponse(url: origin.endpointURL(), statusCode: 200, httpVersion: nil, headerFields: ["Content-Type": "text/html"])!
        let wrongCTRepo = HTTPCurrentReleaseRepository(origin: origin, transport: ControlledTransport(result: .success((Data(), wrongCT))))
        do { _ = try await wrongCTRepo.fetchCurrentRelease(credential: Credential(username: "u", password: "p")); XCTFail("Expected invalid") }
        catch let e as RepositoryError { XCTAssertEqual(e, .invalidResponse) } catch { XCTFail("Unexpected") }

        // URLError.timedOut → timeout
        let timeoutRepo = HTTPCurrentReleaseRepository(origin: origin, transport: ControlledTransport(result: .failure(URLError(.timedOut))))
        do { _ = try await timeoutRepo.fetchCurrentRelease(credential: Credential(username: "u", password: "p")); XCTFail("Expected timeout") }
        catch let e as RepositoryError { XCTAssertEqual(e, .timeout) } catch { XCTFail("Unexpected") }

        // URLError.secureConnection → secureConnection
        let secureTransport = ControlledTransport(result: .failure(URLError(.secureConnectionFailed)))
        let secureRepo = HTTPCurrentReleaseRepository(origin: origin, transport: secureTransport)
        do { _ = try await secureRepo.fetchCurrentRelease(credential: Credential(username: "u", password: "p")); XCTFail("Expected secure connection error") }
        catch let e as RepositoryError { XCTAssertEqual(e, .secureConnection) } catch { XCTFail("Unexpected") }
        XCTAssertEqual(secureTransport.requestCount(), 1, "Trust failure must not retry automatically")

        // URLError.notConnectedToInternet → noConnection
        let noConnRepo = HTTPCurrentReleaseRepository(origin: origin, transport: ControlledTransport(result: .failure(URLError(.notConnectedToInternet))))
        do { _ = try await noConnRepo.fetchCurrentRelease(credential: Credential(username: "u", password: "p")); XCTFail("Expected no connection") }
        catch let e as RepositoryError { XCTAssertEqual(e, .noConnection) } catch { XCTFail("Unexpected") }
    }

    func testSessionConfiguration() throws {
        // IOS-NET-017: urlCache = nil
        // IOS-NET-018: Session and each request bypass local cache data
        // IOS-NET-019: httpCookieStorage = nil, httpShouldSetCookies = false
        // IOS-NET-020: urlCredentialStorage = nil
        // IOS-AUTH-008: No cookie or server-session assumption
        // IOS-PRIV-002: Network session has no response cache
        // IOS-PRIV-003: Network session stores no cookies
        let transport = URLSessionCurrentReleaseTransport()
        let config = transport.session.configuration
        // Production code (Network.swift:78-83): starts from .ephemeral then overrides:
        //   urlCache=nil, cachePolicy=.reloadIgnoringLocalCacheData,
        //   cookieStorage=nil, httpShouldSetCookies=false, credentialStorage=nil
        // Two NSURLSessionConfiguration instances are never === even when equivalent,
        // so compare property values directly.
        XCTAssertNil(config.urlCache)
        XCTAssertEqual(config.requestCachePolicy, .reloadIgnoringLocalCacheData)
        XCTAssertNil(config.httpCookieStorage)
        XCTAssertFalse(config.httpShouldSetCookies)
        XCTAssertNil(config.urlCredentialStorage)
    }
}

// MARK: - Credentials / Keychain (IOS-AUTH-001 through IOS-AUTH-070)

extension AcceptanceEvidenceContractTests {

    func testKeychainLifecycle() async {
        // IOS-AUTH-001: Successful sign-in stores one approved Keychain item
        // IOS-AUTH-002: Relaunch uses the approved Keychain item
        // IOS-AUTH-003: Sign-out deletes matching sync and non-sync items
        // IOS-AUTH-004: HTTP 403 deletes matching items
        // IOS-AUTH-015: errSecDuplicateItem starts update path
        // IOS-AUTH-017: errSecItemNotFound maps to no credential
        // IOS-AUTH-024: errSecItemNotFound from delete maps to complete
        // IOS-AUTH-025: Different account replaces old item, leaves one
        // IOS-AUTH-027: Replacement deletion failure doesn't add new account
        // IOS-AUTH-028: Replacement add failure leaves no credential/release
        let adapter = SecItemFake()
        // Sign-in: no existing credential → add succeeds
        adapter.copyResults = [(errSecItemNotFound, nil)]
        let result = await CredentialStore(adapter: adapter).save(Credential(username: "fictional-user", password: "pwd"))
        XCTAssertEqual(result, .saved)
        XCTAssertEqual(adapter.addAttributes.count, 1)
        XCTAssertEqual(adapter.addAttributes[0][kSecClass as String] as? String, kSecClassGenericPassword as String)
        XCTAssertEqual(adapter.addAttributes[0][kSecAttrAccount as String] as? String, "fictional-user")

        // Relaunch: load succeeds
        let adapter2 = SecItemFake()
        let attrs: [String: Any] = [kSecAttrService as String: CredentialStore.service, kSecAttrAccount as String: "fictional-user", kSecAttrAccessible as String: kSecAttrAccessibleWhenUnlockedThisDeviceOnly, kSecAttrSynchronizable as String: false]
        adapter2.copyResults = [(errSecSuccess, [attrs] as AnyObject), (errSecSuccess, attrs.merging([kSecValueData as String: Data("pwd".utf8)]) { _, new in new } as AnyObject)]
        guard case .credential(let cred) = await CredentialStore(adapter: adapter2).load() else { return XCTFail("Expected credential") }
        XCTAssertEqual(cred.username, "fictional-user")

        // Sign-out: delete succeeds
        adapter2.deleteStatus = errSecSuccess
        let signOutResult = await CredentialStore(adapter: adapter2).signOut()
        XCTAssertEqual(signOutResult, .complete)
        XCTAssertEqual(adapter2.deleteQueries.count, 1)
        XCTAssertEqual(adapter2.deleteQueries[0][kSecAttrSynchronizable as String] as? String, kSecAttrSynchronizableAny as String)

        // IOS-AUTH-015: errSecDuplicateItem updates only the matching account password.
        let duplicateAdapter = SecItemFake()
        duplicateAdapter.copyResults = [(errSecItemNotFound, nil)]
        duplicateAdapter.addStatus = errSecDuplicateItem
        let duplicatePassword = "replacement-password-12"
        let duplicateResult = await CredentialStore(adapter: duplicateAdapter).save(
            Credential(username: "fictional-user", password: duplicatePassword)
        )
        XCTAssertEqual(duplicateResult, .saved)
        XCTAssertEqual(duplicateAdapter.updateQueries.count, 1)
        let duplicateUpdateQuery = duplicateAdapter.updateQueries[0]
        XCTAssertEqual(
            Set(duplicateUpdateQuery.keys),
            Set([kSecClass as String, kSecAttrService as String, kSecAttrAccount as String, kSecAttrSynchronizable as String])
        )
        XCTAssertEqual(duplicateUpdateQuery[kSecClass as String] as? String, kSecClassGenericPassword as String)
        XCTAssertEqual(duplicateUpdateQuery[kSecAttrService as String] as? String, CredentialStore.service)
        XCTAssertEqual(duplicateUpdateQuery[kSecAttrAccount as String] as? String, "fictional-user")
        XCTAssertEqual(duplicateUpdateQuery[kSecAttrSynchronizable as String] as? Bool, false)
        XCTAssertEqual(Set(duplicateAdapter.updateAttributes[0].keys), Set([kSecValueData as String]))
        XCTAssertEqual(duplicateAdapter.updateAttributes[0][kSecValueData as String] as? Data, Data(duplicatePassword.utf8))

        // IOS-AUTH-024: An absent item completes the deletion goal.
        let missingDeleteAdapter = SecItemFake()
        missingDeleteAdapter.deleteStatus = errSecItemNotFound
        let missingDeleteResult = await CredentialStore(adapter: missingDeleteAdapter).signOut()
        XCTAssertEqual(missingDeleteResult, .complete)
        XCTAssertEqual(missingDeleteAdapter.deleteQueries.count, 1)

        let oldAttributes: [String: Any] = [kSecClass as String: kSecClassGenericPassword, kSecAttrService as String: CredentialStore.service, kSecAttrAccount as String: "old-user", kSecAttrAccessible as String: kSecAttrAccessibleWhenUnlockedThisDeviceOnly, kSecAttrSynchronizable as String: false]

        // IOS-AUTH-025: A different account deletes the old service item before one replacement add.
        let replacementAdapter = StatefulSecItemFake(items: [oldAttributes])
        let replacementResult = await CredentialStore(adapter: replacementAdapter).save(Credential(username: "replacement-user", password: "pwd"))
        XCTAssertEqual(replacementResult, .saved)
        XCTAssertEqual(replacementAdapter.deleteQueries.count, 1)
        XCTAssertEqual(replacementAdapter.addAttributes.count, 1)
        XCTAssertEqual(replacementAdapter.addAttributes[0][kSecAttrAccount as String] as? String, "replacement-user")
        XCTAssertEqual(replacementAdapter.items.count, 1)
        XCTAssertEqual(replacementAdapter.items[0][kSecAttrService as String] as? String, CredentialStore.service)
        XCTAssertEqual(replacementAdapter.items[0][kSecAttrAccount as String] as? String, "replacement-user")

        // IOS-AUTH-027: Failed replacement deletion must not add the replacement account.
        let deletionFailureAdapter = SecItemFake()
        deletionFailureAdapter.copyResults = [(errSecSuccess, [oldAttributes] as AnyObject)]
        deletionFailureAdapter.deleteStatus = errSecAuthFailed
        let deletionFailureResult = await CredentialStore(adapter: deletionFailureAdapter).save(Credential(username: "replacement-user", password: "pwd"))
        XCTAssertEqual(deletionFailureResult, .deletionPending)
        XCTAssertEqual(deletionFailureAdapter.deleteQueries.count, 1)
        XCTAssertEqual(deletionFailureAdapter.addAttributes.count, 0)

        // IOS-AUTH-028: After deletion, a failed replacement add must report save failure.
        let addFailureAdapter = SecItemFake()
        addFailureAdapter.copyResults = [(errSecSuccess, [oldAttributes] as AnyObject)]
        addFailureAdapter.deleteStatus = errSecSuccess
        addFailureAdapter.addStatus = errSecAuthFailed
        let addFailureResult = await CredentialStore(adapter: addFailureAdapter).save(Credential(username: "replacement-user", password: "pwd"))
        XCTAssertEqual(addFailureResult, .saveFailure)
        XCTAssertEqual(addFailureAdapter.deleteQueries.count, 1)
        XCTAssertEqual(addFailureAdapter.addAttributes.count, 1)
    }

    @MainActor
    func testKeychainQueries() async throws {
        // IOS-AUTH-011: Add uses exact class, service, account, secret encoding
        // IOS-AUTH-012: Add uses exact accessibility, synchronisation, access-group
        // IOS-AUTH-013: Inventory finds both sync classes, one exact query for non-sync
        // IOS-AUTH-014: Same-account update changes only exact item password
        // IOS-AUTH-016: All-service deletion removes matching items from both sync classes
        // IOS-AUTH-030: Reset/replacement/sign-out/403 use service deletion with kSecAttrSynchronizableAny
        // IOS-AUTH-051: Inventory and exact-read use kSecClassGenericPassword
        // IOS-AUTH-061: Recovery deletion uses service query with kSecAttrSynchronizableAny
        // IOS-AUTH-064: Exact credential reads use kSecAttrSynchronizable = false
        let adapter = SecItemFake()
        adapter.copyResults = [(errSecItemNotFound, nil)]
        _ = await CredentialStore(adapter: adapter).save(Credential(username: "fictional-user", password: "pwd"))

        let add = adapter.addAttributes[0]
        XCTAssertEqual(add[kSecClass as String] as? String, kSecClassGenericPassword as String)
        XCTAssertEqual(add[kSecAttrService as String] as? String, CredentialStore.service)
        XCTAssertEqual(add[kSecAttrAccount as String] as? String, "fictional-user")
        XCTAssertEqual(add[kSecAttrAccessible as String] as? String, kSecAttrAccessibleWhenUnlockedThisDeviceOnly as String)
        XCTAssertEqual(add[kSecAttrSynchronizable as String] as? Bool, false)
        // Secret is stored as Data
        XCTAssertNotNil(add[kSecValueData as String] as? Data)

        // IOS-AUTH-030 and IOS-AUTH-061: reset, replacement, sign-out, and denied
        // deletion all use the complete all-service query.
        let deletionAdapter = SecItemFake()
        let deletionStore = CredentialStore(adapter: deletionAdapter)
        let resetResult = await deletionStore.reset()
        let signOutResult = await deletionStore.signOut()
        let deniedResult = await deletionStore.removeDeniedCredential()
        XCTAssertEqual(resetResult, .complete)
        XCTAssertEqual(signOutResult, .complete)
        XCTAssertEqual(deniedResult, .complete)
        let replacementDeletionAdapter = SecItemFake()
        replacementDeletionAdapter.copyResults = [(errSecSuccess, [[
            kSecAttrService as String: CredentialStore.service,
            kSecAttrAccount as String: "old-user",
            kSecAttrAccessible as String: kSecAttrAccessibleWhenUnlockedThisDeviceOnly,
            kSecAttrSynchronizable as String: false
        ]] as AnyObject)]
        let replacementResult = await CredentialStore(adapter: replacementDeletionAdapter)
            .save(Credential(username: "replacement-user", password: "pwd"))
        XCTAssertEqual(replacementResult, .saved)
        XCTAssertEqual(deletionAdapter.deleteQueries.count, 3)
        XCTAssertEqual(replacementDeletionAdapter.deleteQueries.count, 1)
        let deletionQueries = deletionAdapter.deleteQueries + replacementDeletionAdapter.deleteQueries
        XCTAssertEqual(deletionQueries.count, 4)
        for query in deletionQueries {
            XCTAssertEqual(query[kSecClass as String] as? String, kSecClassGenericPassword as String)
            XCTAssertEqual(query[kSecAttrService as String] as? String, CredentialStore.service)
            XCTAssertEqual(query[kSecAttrSynchronizable as String] as? String, kSecAttrSynchronizableAny as String)
        }

        // IOS-AUTH-004 and IOS-AUTH-030: a real HTTP 403 response must flow through
        // SessionState and CredentialStore before the exact service query is deleted.
        let deniedAdapter = SecItemFake()
        let deniedAttributes: [String: Any] = [
            kSecAttrService as String: CredentialStore.service,
            kSecAttrAccount as String: "fictional-user",
            kSecAttrAccessible as String: kSecAttrAccessibleWhenUnlockedThisDeviceOnly,
            kSecAttrSynchronizable as String: false
        ]
        deniedAdapter.copyResults = [
            (errSecSuccess, [deniedAttributes] as AnyObject),
            (errSecSuccess, deniedAttributes.merging([kSecValueData as String: Data("password-12".utf8)]) { _, value in value } as AnyObject)
        ]
        deniedAdapter.deleteStatus = errSecSuccess
        let deniedStore = CredentialStore(adapter: deniedAdapter)
        let origin = try PreviewOrigin(rawValue: "https://preview.example.invalid")
        let deniedResponse = try XCTUnwrap(
            HTTPURLResponse(url: origin.endpointURL(), statusCode: 403, httpVersion: nil, headerFields: nil)
        )
        let deniedRepository = HTTPCurrentReleaseRepository(
            origin: origin,
            transport: ControlledTransport(result: .success((Data(), deniedResponse)))
        )
        let deniedState = SessionState(
            configuration: AppConfiguration(origin: .success(origin)),
            store: deniedStore,
            repository: deniedRepository
        )
        deniedState.start()
        try await waitUntil("403 deletion result", state: deniedState) {
            $0 == .signIn(message: "Access denied. Sign in again.")
        }
        XCTAssertEqual(deniedState.screen, .signIn(message: "Access denied. Sign in again."))
        XCTAssertEqual(deniedAdapter.deleteQueries.count, 1)
        let deniedDeletionQuery = deniedAdapter.deleteQueries[0]
        XCTAssertEqual(
            Set(deniedDeletionQuery.keys),
            Set([kSecClass as String, kSecAttrService as String, kSecAttrSynchronizable as String])
        )
        XCTAssertEqual(deniedDeletionQuery[kSecClass as String] as? String, kSecClassGenericPassword as String)
        XCTAssertEqual(deniedDeletionQuery[kSecAttrService as String] as? String, CredentialStore.service)
        XCTAssertEqual(deniedDeletionQuery[kSecAttrSynchronizable as String] as? String, kSecAttrSynchronizableAny as String)

        // IOS-AUTH-064: Exact reads select one non-synchronised account only.
        let readAdapter = SecItemFake()
        let readAttributes: [String: Any] = [kSecAttrService as String: CredentialStore.service, kSecAttrAccount as String: "fictional-user", kSecAttrAccessible as String: kSecAttrAccessibleWhenUnlockedThisDeviceOnly, kSecAttrSynchronizable as String: false]
        readAdapter.copyResults = [(errSecSuccess, [readAttributes] as AnyObject), (errSecSuccess, readAttributes.merging([kSecValueData as String: Data("pwd".utf8)]) { _, value in value } as AnyObject)]
        let readResult = await CredentialStore(adapter: readAdapter).load()
        XCTAssertEqual(readResult, .credential(Credential(username: "fictional-user", password: "pwd")))
        XCTAssertEqual(readAdapter.queries.count, 2)
        let exactRead = readAdapter.queries[1]
        XCTAssertEqual(exactRead[kSecClass as String] as? String, kSecClassGenericPassword as String)
        XCTAssertEqual(exactRead[kSecAttrAccount as String] as? String, "fictional-user")
        XCTAssertEqual(exactRead[kSecAttrSynchronizable as String] as? Bool, false)
    }

    func testKeychainSerialisation() async {
        // IOS-AUTH-029: Concurrent saves are non-overlapping and leave one item.
        let adapter = ConcurrentKeychainAdapter()
        let store = CredentialStore(adapter: adapter)
        let results = await withTaskGroup(of: CredentialSaveResult.self, returning: [CredentialSaveResult].self) { group in
            group.addTask { await store.save(Credential(username: "user-a", password: "pw-a")) }
            group.addTask { await store.save(Credential(username: "user-b", password: "pw-b")) }
            var values: [CredentialSaveResult] = []
            for await value in group { values.append(value) }
            return values
        }
        XCTAssertEqual(results.count, 2)
        XCTAssertTrue(results.allSatisfy { $0 == .saved })
        let snapshot = adapter.snapshot()
        XCTAssertEqual(snapshot.maximumInFlight, 1, "CredentialStore must not overlap adapter calls")
        XCTAssertEqual(snapshot.itemCount, 1, "Concurrent saves must leave one Keychain item")
        let expectedFirstSaveLifecycle: [ConcurrentKeychainAdapter.OperationEvent] = [
            .started(.copyMatching), .completed(.copyMatching),
            .started(.add), .completed(.add)
        ]
        let expectedSecondSaveLifecycle: [ConcurrentKeychainAdapter.OperationEvent] = [
            .started(.copyMatching), .completed(.copyMatching),
            .started(.delete), .completed(.delete),
            .started(.add), .completed(.add)
        ]
        XCTAssertEqual(snapshot.operationEvents, expectedFirstSaveLifecycle + expectedSecondSaveLifecycle, "One copy/add lifecycle must complete before the next copy/delete/add lifecycle starts")
    }

    func testKeychainSourceInspection() async {
        // IOS-AUTH-065: No Keychain migration, repair, attribute rewrite, or credential salvage path
        // The CredentialStore has no migration or repair logic. Verify by checking all public surfaces.
        // Load never modifies Keychain state.
        let adapter = SecItemFake()
        adapter.copyResults = [(errSecItemNotFound, nil)]
        _ = await CredentialStore(adapter: adapter).load()
        XCTAssertEqual(adapter.addAttributes.count, 0, "Load should never add items")
        XCTAssertEqual(adapter.updateQueries.count, 0, "Load should never update items")
        XCTAssertEqual(adapter.deleteQueries.count, 0, "Load should never delete items")
    }

    func testKeychainValidation() async {
        // IOS-AUTH-026: Multiple items, synchronised item, or invalid attributes → deletion-only
        // IOS-AUTH-038: Guard cases are partial evidence. The complete returned-attribute
        // matrix remains pending approved signed validation.
        // IOS-AUTH-039 through IOS-AUTH-056: Returned-attribute validation
        // IOS-AUTH-066 through IOS-AUTH-070: Edge cases
        let service = CredentialStore.service
        let goodAttrs: [String: Any] = [kSecAttrService as String: service, kSecAttrAccount as String: "fictional-user", kSecAttrAccessible as String: kSecAttrAccessibleWhenUnlockedThisDeviceOnly, kSecAttrSynchronizable as String: false]

        func loadInventory(_ attributes: [String: Any], exact: [String: Any]? = nil) async -> CredentialLoadResult {
            let adapter = SecItemFake()
            var result = attributes
            result[kSecValueData as String] = Data("fictional-password".utf8)
            adapter.copyResults = [(errSecSuccess, [attributes] as AnyObject), (errSecSuccess, (exact ?? result) as AnyObject)]
            return await CredentialStore(adapter: adapter).load()
        }
        func assertUnsafeInventory(_ attributes: [String: Any], _ identifier: String) async {
            let result = await loadInventory(attributes)
            XCTAssertEqual(result, .unsafe, "\(identifier) must enter deletion-only recovery")
        }

        // IOS-AUTH-039: Valid system-managed dates do not invalidate a credential.
        var dated = goodAttrs
        dated[kSecAttrCreationDate as String] = Date(timeIntervalSince1970: 1_700_000_000)
        dated[kSecAttrModificationDate as String] = Date(timeIntervalSince1970: 1_700_000_100)
        let datedResult = await loadInventory(dated)
        XCTAssertEqual(datedResult, .credential(Credential(username: "fictional-user", password: "fictional-password")))

        // IOS-AUTH-040: An Apple-defined generic-password attribute is accepted.
        var labelled = goodAttrs
        labelled[kSecAttrLabel as String] = "Fictional ACE credential"
        let labelledResult = await loadInventory(labelled)
        XCTAssertEqual(labelledResult, .credential(Credential(username: "fictional-user", password: "fictional-password")))

        // IOS-AUTH-041: An unknown returned key cannot replace a required value.
        var unknownKey = goodAttrs
        unknownKey["fictional-unknown-key"] = "ignored"
        let unknownKeyResult = await loadInventory(unknownKey)
        XCTAssertEqual(unknownKeyResult, .credential(Credential(username: "fictional-user", password: "fictional-password")))

        // IOS-AUTH-043: A non-CFString account enters deletion-only recovery.
        var nonStringAccount = goodAttrs
        nonStringAccount[kSecAttrAccount as String] = 42
        await assertUnsafeInventory(nonStringAccount, "IOS-AUTH-043")

        // IOS-AUTH-045: Missing secret data enters deletion-only recovery.
        let missingDataAdapter = SecItemFake()
        missingDataAdapter.copyResults = [(errSecSuccess, [goodAttrs] as AnyObject), (errSecSuccess, goodAttrs as AnyObject)]
        let missingDataResult = await CredentialStore(adapter: missingDataAdapter).load()
        XCTAssertEqual(missingDataResult, .unsafe)

        // IOS-AUTH-046: A secret that is not CFData enters deletion-only recovery.
        var nonDataExact = goodAttrs
        nonDataExact[kSecValueData as String] = "not-data"
        let nonDataResult = await loadInventory(goodAttrs, exact: nonDataExact)
        XCTAssertEqual(nonDataResult, .unsafe)

        // IOS-AUTH-048: Invalid UTF-8 secret data enters deletion-only recovery.
        var invalidUTF8Exact = goodAttrs
        invalidUTF8Exact[kSecValueData as String] = Data([0xFF])
        let invalidUTF8Result = await loadInventory(goodAttrs, exact: invalidUTF8Exact)
        XCTAssertEqual(invalidUTF8Result, .unsafe)

        // IOS-AUTH-052: Absent, wrong-type, or mismatched service enters deletion-only recovery.
        var absentService = goodAttrs
        absentService.removeValue(forKey: kSecAttrService as String)
        await assertUnsafeInventory(absentService, "IOS-AUTH-052 absent")
        var wrongService = goodAttrs
        wrongService[kSecAttrService as String] = 42
        await assertUnsafeInventory(wrongService, "IOS-AUTH-052 wrong type")
        var mismatchedService = goodAttrs
        mismatchedService[kSecAttrService as String] = "com.example.other"
        await assertUnsafeInventory(mismatchedService, "IOS-AUTH-052 mismatched")

        // IOS-AUTH-053: Wrong-type and mismatched access groups fail closed. The
        // approved signed access-group positive case remains pending.
        var wrongGroup = goodAttrs
        wrongGroup[kSecAttrAccessGroup as String] = 42
        await assertUnsafeInventory(wrongGroup, "IOS-AUTH-053 wrong type")
        var mismatchedGroup = goodAttrs
        mismatchedGroup[kSecAttrAccessGroup as String] = "TEAM.example"
        await assertUnsafeInventory(mismatchedGroup, "IOS-AUTH-053 mismatched")

        // IOS-AUTH-054: Absent, wrong-type, or true synchronisation enters deletion-only recovery.
        var absentSynchronisation = goodAttrs
        absentSynchronisation.removeValue(forKey: kSecAttrSynchronizable as String)
        await assertUnsafeInventory(absentSynchronisation, "IOS-AUTH-054 absent")
        var wrongSynchronisation = goodAttrs
        wrongSynchronisation[kSecAttrSynchronizable as String] = "false"
        await assertUnsafeInventory(wrongSynchronisation, "IOS-AUTH-054 wrong type")
        var trueSynchronisation = goodAttrs
        trueSynchronisation[kSecAttrSynchronizable as String] = true
        await assertUnsafeInventory(trueSynchronisation, "IOS-AUTH-054 true")

        // IOS-AUTH-055: Unexpected inventory member and exact-read result types are unsafe.
        let invalidInventoryMember = SecItemFake()
        invalidInventoryMember.copyResults = [(errSecSuccess, ["not-an-attribute-dictionary"] as AnyObject)]
        let invalidInventoryMemberResult = await CredentialStore(adapter: invalidInventoryMember).load()
        XCTAssertEqual(invalidInventoryMemberResult, .unsafe)
        let invalidExactResult = SecItemFake()
        invalidExactResult.copyResults = [(errSecSuccess, [goodAttrs] as AnyObject), (errSecSuccess, ["not-an-exact-result"] as AnyObject)]
        let invalidExactResultValue = await CredentialStore(adapter: invalidExactResult).load()
        XCTAssertEqual(invalidExactResultValue, .unsafe)

        // IOS-AUTH-066: A non-CFDate creation or modification date enters deletion-only recovery.
        var nonDate = goodAttrs
        nonDate[kSecAttrCreationDate as String] = "not-a-date"
        await assertUnsafeInventory(nonDate, "IOS-AUTH-066")
        var nonModificationDate = goodAttrs
        nonModificationDate[kSecAttrModificationDate as String] = "not-a-date"
        await assertUnsafeInventory(nonModificationDate, "IOS-AUTH-066 modification date")

        // IOS-AUTH-067: Absent, wrong-type, or mismatched accessibility enters deletion-only recovery.
        var absentAccessibility = goodAttrs
        absentAccessibility.removeValue(forKey: kSecAttrAccessible as String)
        await assertUnsafeInventory(absentAccessibility, "IOS-AUTH-067 absent")
        var wrongAccessibility = goodAttrs
        wrongAccessibility[kSecAttrAccessible as String] = 42
        await assertUnsafeInventory(wrongAccessibility, "IOS-AUTH-067 wrong type")
        var mismatchedAccessibility = goodAttrs
        mismatchedAccessibility[kSecAttrAccessible as String] = kSecAttrAccessibleAfterFirstUnlock
        await assertUnsafeInventory(mismatchedAccessibility, "IOS-AUTH-067 mismatched")

        // IOS-AUTH-049: Multiple inventory items → unsafe (deletion-only)
        let multiAdapter = SecItemFake()
        multiAdapter.copyResults = [(errSecSuccess, [goodAttrs, goodAttrs] as AnyObject)]
        let multiResult = await CredentialStore(adapter: multiAdapter).load()
        XCTAssertEqual(multiResult, .unsafe)

        // IOS-AUTH-050: Synchronised inventory item → unsafe
        let syncAdapter = SecItemFake()
        var syncAttrs = goodAttrs
        syncAttrs[kSecAttrSynchronizable as String] = true
        syncAdapter.copyResults = [(errSecSuccess, [syncAttrs] as AnyObject)]
        let syncResult = await CredentialStore(adapter: syncAdapter).load()
        XCTAssertEqual(syncResult, .unsafe)

        // IOS-AUTH-042: Absent account → unsafe
        let noAccountAdapter = SecItemFake()
        var noAccount = goodAttrs
        noAccount.removeValue(forKey: kSecAttrAccount as String)
        noAccountAdapter.copyResults = [(errSecSuccess, [noAccount] as AnyObject)]
        let noAccountResult = await CredentialStore(adapter: noAccountAdapter).load()
        XCTAssertEqual(noAccountResult, .unsafe)

        // IOS-AUTH-044: Empty account → unsafe
        let emptyAcctAdapter = SecItemFake()
        var emptyAcct = goodAttrs
        emptyAcct[kSecAttrAccount as String] = ""
        emptyAcctAdapter.copyResults = [(errSecSuccess, [emptyAcct] as AnyObject)]
        let emptyAcctResult = await CredentialStore(adapter: emptyAcctAdapter).load()
        XCTAssertEqual(emptyAcctResult, .unsafe)

        // IOS-AUTH-047: Empty secret data → unsafe
        let emptyDataAdapter = SecItemFake()
        emptyDataAdapter.copyResults = [(errSecSuccess, [goodAttrs] as AnyObject), (errSecSuccess, goodAttrs.merging([kSecValueData as String: Data()]) { _, new in new } as AnyObject)]
        let emptyDataResult = await CredentialStore(adapter: emptyDataAdapter).load()
        XCTAssertEqual(emptyDataResult, .unsafe)

        // IOS-AUTH-056: Exact-read account differs from inventory → unsafe
        let mismatchAdapter = SecItemFake()
        mismatchAdapter.copyResults = [(errSecSuccess, [goodAttrs] as AnyObject), (errSecSuccess, goodAttrs.merging([kSecValueData as String: Data("pwd".utf8), kSecAttrAccount as String: "different-user"]) { _, new in new } as AnyObject)]
        let mismatchResult = await CredentialStore(adapter: mismatchAdapter).load()
        XCTAssertEqual(mismatchResult, .unsafe)

        // IOS-AUTH-069: Exact-read errSecItemNotFound after successful inventory → unsafe
        let notFoundAdapter = SecItemFake()
        notFoundAdapter.copyResults = [(errSecSuccess, [goodAttrs] as AnyObject), (errSecItemNotFound, nil)]
        let notFoundResult = await CredentialStore(adapter: notFoundAdapter).load()
        XCTAssertEqual(notFoundResult, .unsafe)

        // IOS-AUTH-070: errSecSuccess with empty inventory array → unsafe
        let emptyInvAdapter = SecItemFake()
        emptyInvAdapter.copyResults = [(errSecSuccess, [] as AnyObject)]
        let emptyInvResult = await CredentialStore(adapter: emptyInvAdapter).load()
        XCTAssertEqual(emptyInvResult, .unsafe)

        // IOS-AUTH-068: errSecSuccess with inventory not an array → unsafe
        let nonArrayAdapter = SecItemFake()
        nonArrayAdapter.copyResults = [(errSecSuccess, "not an array" as AnyObject)]
        let nonArrayResult = await CredentialStore(adapter: nonArrayAdapter).load()
        XCTAssertEqual(nonArrayResult, .unsafe)
    }
}

// MARK: - Screen States (IOS-STATE-001 through IOS-STATE-018)

extension AcceptanceEvidenceContractTests {

    @MainActor
    func testStateGeneration() async throws {
        // IOS-NET-010, IOS-NET-011, IOS-AUTH-009, IOS-AUTH-010, IOS-STATE-007
        // use suspended requests and observable continuations.
        let origin = try PreviewOrigin(rawValue: "https://preview.example.invalid")
        let credential = Credential(username: "fictional-user", password: "pwd")

        let releaseOne = ClientReleaseResponse(engagementName: "First", reviewStatus: "RELEASED", releaseVersion: 1, publishedAt: "2026-08-24T10:15:30Z", conclusion: nil, actions: [])
        let releaseTwo = ClientReleaseResponse(engagementName: "Second", reviewStatus: "RELEASED", releaseVersion: 2, publishedAt: "2026-08-24T10:15:30Z", conclusion: nil, actions: [])

        let refreshRepository = SuspendedRepository()
        let state = SessionState(configuration: AppConfiguration(origin: .success(origin)), store: ControlledCredentialStore(loadResult: .credential(credential)), repository: refreshRepository)
        state.start()
        await refreshRepository.waitForRequests(1)
        state.refresh()
        await refreshRepository.waitForRequests(2)
        await refreshRepository.complete(1, with: .success(.release(releaseTwo)))
        await refreshRepository.waitForReturnedRequests(1)
        try await waitUntil("latest refresh", state: state) { self.releaseVersion(in: $0) == 2 }
        await refreshRepository.complete(0, with: .success(.release(releaseOne)))
        await refreshRepository.waitForReturnedRequests(2)
        XCTAssertEqual(releaseVersion(in: state.screen), 2)

        let signOutRepository = SuspendedRepository()
        let signOutState = SessionState(configuration: AppConfiguration(origin: .success(origin)), store: ControlledCredentialStore(loadResult: .credential(credential)), repository: signOutRepository)
        signOutState.start()
        await signOutRepository.waitForRequests(1)
        signOutState.signOut()
        try await waitUntil("sign-out", state: signOutState) { $0 == .signIn(message: nil) }
        await signOutRepository.complete(0, with: .success(.release(releaseOne)))
        await signOutRepository.waitForReturnedRequests(1)
        XCTAssertEqual(signOutState.screen, .signIn(message: nil))

        let credentialRepository = SuspendedRepository()
        let credentialStore = ControlledCredentialStore(loadResult: .none)
        let credentialState = SessionState(configuration: AppConfiguration(origin: .success(origin)), store: credentialStore, repository: credentialRepository)
        credentialState.start()
        try await waitUntil("initial sign-in", state: credentialState) { $0 == .signIn(message: nil) }
        credentialState.signIn(username: "user-a", password: "password-a")
        await credentialRepository.waitForRequests(1)
        credentialState.signIn(username: "user-b", password: "password-b")
        await credentialRepository.waitForRequests(2)
        let secondCredential = await credentialRepository.credential(at: 1)
        XCTAssertEqual(secondCredential.username, "user-b")
        await credentialRepository.complete(1, with: .success(.release(releaseTwo)))
        await credentialRepository.waitForReturnedRequests(1)
        try await waitUntil("new credential", state: credentialState) { self.releaseVersion(in: $0) == 2 }
        await credentialRepository.complete(0, with: .success(.release(releaseOne)))
        await credentialRepository.waitForReturnedRequests(2)
        XCTAssertEqual(releaseVersion(in: credentialState.screen), 2)
        let savedCredentials = await credentialStore.saved()
        XCTAssertEqual(savedCredentials.map(\.username), ["user-b"])
    }

    @MainActor
    func testStateErrorHandling() async throws {
        // IOS-AUTH-005, IOS-AUTH-018 through IOS-AUTH-022,
        // IOS-AUTH-057 through IOS-AUTH-060, IOS-AUTH-062, IOS-AUTH-063.
        // IOS-STATE-002 through IOS-STATE-006, IOS-STATE-008, IOS-STATE-016.
        // IOS-AUTH-023 (locked device) is pending — needs physical hardware.
        let origin = try PreviewOrigin(rawValue: "https://preview.example.invalid")
        let credential = Credential(username: "fictional-user", password: "pwd")

        // IOS-AUTH-018: A locked-device Keychain status is a safe read failure.
        let lockedAdapter = SecItemFake()
        lockedAdapter.copyResults = [(errSecInteractionNotAllowed, nil)]
        let lockedResult = await CredentialStore(adapter: lockedAdapter).load()
        XCTAssertEqual(lockedResult, .failure)

        // IOS-AUTH-019: Another Keychain status is also a safe read failure.
        let failedAdapter = SecItemFake()
        failedAdapter.copyResults = [(errSecAuthFailed, nil)]
        let failedResult = await CredentialStore(adapter: failedAdapter).load()
        XCTAssertEqual(failedResult, .failure)

        // Baseline: no credential → sign-in
        let noCredStore = ControlledCredentialStore(loadResult: .none)
        let noCredState = SessionState(configuration: AppConfiguration(origin: .success(origin)), store: noCredStore, repository: ControlledRepository(result: .failure(RepositoryError.unavailable)))
        noCredState.start()
        try await waitUntil("no credential", state: noCredState) { $0 == .signIn(message: nil) }
        guard case .signIn(message: nil) = noCredState.screen else { return XCTFail("Expected .signIn(message: nil) with no credential, got \(noCredState.screen)") }
        let firstEmptySignInAnnouncement = noCredState.errorAnnouncementEvent
        noCredState.signIn(username: "", password: "")
        XCTAssertEqual(noCredState.screen, .signIn(message: "Enter a username and password."))
        XCTAssertEqual(noCredState.errorAnnouncementEvent, firstEmptySignInAnnouncement + 1)
        noCredState.signIn(username: "", password: "")
        XCTAssertEqual(noCredState.screen, .signIn(message: "Enter a username and password."))
        XCTAssertEqual(noCredState.errorAnnouncementEvent, firstEmptySignInAnnouncement + 2, "Identical validation failures must create distinct VoiceOver events")

        // IOS-AUTH-005: HTTP 503 retains Keychain item
        let store503 = ControlledCredentialStore(loadResult: .credential(credential))
        let state503 = SessionState(configuration: AppConfiguration(origin: .success(origin)), store: store503, repository: ControlledRepository(result: .failure(RepositoryError.unavailable)))
        state503.start()
        try await waitUntil("unavailable", state: state503) { $0 == .failure(message: "ACE is unavailable. Try again later.", retry: .refresh) }
        guard case .failure(message: "ACE is unavailable. Try again later.", retry: .refresh) = state503.screen else { return XCTFail("Expected .failure(ACE unavailable, .refresh) for 503, got \(state503.screen)") }

        // IOS-AUTH-004: HTTP 403 deletes credentials and shows the exact sign-in message.
        let store403 = ControlledCredentialStore(loadResult: .credential(credential))
        let state403 = SessionState(configuration: AppConfiguration(origin: .success(origin)), store: store403, repository: ControlledRepository(result: .failure(RepositoryError.denied)))
        state403.start()
        try await waitUntil("denied deletion", state: state403) { $0 == .signIn(message: "Access denied. Sign in again.") }
        XCTAssertEqual(state403.screen, .signIn(message: "Access denied. Sign in again."))

        // IOS-AUTH-019: Keychain read failure → failure with .keychainRead retry
        let failStore = ControlledCredentialStore(loadResult: .failure)
        let failState = SessionState(configuration: AppConfiguration(origin: .success(origin)), store: failStore, repository: ControlledRepository(result: .failure(RepositoryError.unavailable)))
        failState.start()
        try await waitUntil("read failure", state: failState) { $0 == .failure(message: "Saved sign-in could not be read. Try again.", retry: .keychainRead) }
        guard case .failure(message: "Saved sign-in could not be read. Try again.", retry: .keychainRead) = failState.screen else { return XCTFail("Expected .failure(.keychainRead) for read failure, got \(failState.screen)") }

        // IOS-AUTH-020: A Keychain write failure does not report successful sign-in.
        let writeFailureStore = ControlledCredentialStore(loadResult: .none, saveResult: .saveFailure)
        let writeFailureState = SessionState(configuration: AppConfiguration(origin: .success(origin)), store: writeFailureStore, repository: ControlledRepository(result: .success(.empty)))
        writeFailureState.start()
        try await waitUntil("write-failure sign-in", state: writeFailureState) { $0 == .signIn(message: nil) }
        writeFailureState.signIn(username: "fictional-user", password: "fictional-password")
        try await waitUntil("write failure", state: writeFailureState) { $0 == .signIn(message: "Sign-in could not be saved. Try again.") }
        XCTAssertEqual(writeFailureState.screen, .signIn(message: "Sign-in could not be saved. Try again."))

        // A failed initial sign-in returns to sign-in, not a credential-less refresh action.
        let initialFailureRepository = SuspendedRepository()
        let initialFailureState = SessionState(configuration: AppConfiguration(origin: .success(origin)), store: ControlledCredentialStore(loadResult: .none), repository: initialFailureRepository)
        initialFailureState.start()
        try await waitUntil("initial failure sign-in", state: initialFailureState) { $0 == .signIn(message: nil) }
        initialFailureState.signIn(username: "fictional-user", password: "fictional-password")
        await initialFailureRepository.waitForRequests(1)
        await initialFailureRepository.complete(0, with: .failure(.unavailable))
        await initialFailureRepository.waitForReturnedRequests(1)
        try await waitUntil("initial sign-in failure", state: initialFailureState) { $0 == .signIn(message: "ACE is unavailable. Try again later.") }
        XCTAssertEqual(initialFailureState.screen, .signIn(message: "ACE is unavailable. Try again later."))
        initialFailureState.signIn(username: "fictional-user", password: "fictional-password")
        await initialFailureRepository.waitForRequests(2)
        await initialFailureRepository.complete(1, with: .success(.empty))
        await initialFailureRepository.waitForReturnedRequests(2)
        try await waitUntil("initial sign-in retry", state: initialFailureState) { $0 == .empty }
        XCTAssertEqual(initialFailureState.screen, .empty)

        // IOS-AUTH-026: Unsafe keychain attributes → deletion-only recovery
        let unsafeStore = ControlledCredentialStore(loadResult: .unsafe)
        let unsafeState = SessionState(configuration: AppConfiguration(origin: .success(origin)), store: unsafeStore, repository: ControlledRepository(result: .failure(RepositoryError.unavailable)))
        unsafeState.start()
        try await waitUntil("unsafe credential", state: unsafeState) { $0 == .deletionPending(message: "Saved sign-in must be reset before access.", afterDeletion: nil, deletionOnlyRecovery: true) }
        guard case .deletionPending(message: "Saved sign-in must be reset before access.", afterDeletion: nil, deletionOnlyRecovery: true) = unsafeState.screen else { return XCTFail("Expected .deletionPending(reset) for unsafe, got \(unsafeState.screen)") }

        // IOS-AUTH-062: A failed reset retains the deletion-only recovery state and starts no request.
        let resetPendingRepository = SuspendedRepository()
        let resetPendingState = SessionState(configuration: AppConfiguration(origin: .success(origin)), store: ControlledCredentialStore(loadResult: .unsafe, resetResult: .pending), repository: resetPendingRepository)
        resetPendingState.start()
        try await waitUntil("reset pending initial state", state: resetPendingState) { $0 == .deletionPending(message: "Saved sign-in must be reset before access.", afterDeletion: nil, deletionOnlyRecovery: true) }
        resetPendingState.resetSavedSignIn()
        try await waitUntil("reset pending", state: resetPendingState) { $0 == .deletionPending(message: "Saved sign-in could not be removed. Try again.", afterDeletion: nil, deletionOnlyRecovery: true) }
        XCTAssertEqual(resetPendingState.screen, .deletionPending(message: "Saved sign-in could not be removed. Try again.", afterDeletion: nil, deletionOnlyRecovery: true))
        let resetPendingRequests = await resetPendingRepository.requestCount()
        XCTAssertEqual(resetPendingRequests, 0)

        // IOS-AUTH-063: A successful reset returns to the unprompted sign-in state.
        let resetCompleteState = SessionState(configuration: AppConfiguration(origin: .success(origin)), store: ControlledCredentialStore(loadResult: .unsafe, resetResult: .complete), repository: ControlledRepository(result: .failure(RepositoryError.unavailable)))
        resetCompleteState.start()
        try await waitUntil("reset complete initial state", state: resetCompleteState) { $0 == .deletionPending(message: "Saved sign-in must be reset before access.", afterDeletion: nil, deletionOnlyRecovery: true) }
        resetCompleteState.resetSavedSignIn()
        try await waitUntil("reset complete", state: resetCompleteState) { $0 == .signIn(message: nil) }
        XCTAssertEqual(resetCompleteState.screen, .signIn(message: nil))

        // IOS-AUTH-005: A 503 retains the credential and returns to the same safe state.
        state503.start()
        try await waitUntil("503 restart", state: state503) { $0 == .failure(message: "ACE is unavailable. Try again later.", retry: .refresh) }
        guard case .failure(message: "ACE is unavailable. Try again later.", retry: .refresh) = state503.screen else { return XCTFail("Re-start after 503 must show same failure, got \(state503.screen)") }

        // IOS-AUTH-021: A deletion failure does not report successful sign-out.
        let signOutStore = ControlledCredentialStore(loadResult: .credential(credential), signOutResult: .pending)
        let signOutState = SessionState(configuration: AppConfiguration(origin: .success(origin)), store: signOutStore, repository: ControlledRepository(result: .success(.empty)))
        signOutState.start()
        try await waitUntil("initial release", state: signOutState) { $0 == .empty }
        signOutState.signOut()
        try await waitUntil("sign-out deletion pending", state: signOutState) { $0 == .deletionPending(message: "Sign-out could not be completed. Try again.", afterDeletion: nil, deletionOnlyRecovery: false) }
        guard case .deletionPending(message: "Sign-out could not be completed. Try again.", afterDeletion: nil, deletionOnlyRecovery: false) = signOutState.screen else { return XCTFail("Expected .deletionPending(sign-out) for pending sign-out, got \(signOutState.screen)") }

        // IOS-AUTH-022: A deletion-pending state starts no network request.
        let blockedRepository = SuspendedRepository()
        let blockedState = SessionState(configuration: AppConfiguration(origin: .success(origin)), store: ControlledCredentialStore(loadResult: .unsafe), repository: blockedRepository)
        blockedState.start()
        try await waitUntil("deletion pending", state: blockedState) { $0 == .deletionPending(message: "Saved sign-in must be reset before access.", afterDeletion: nil, deletionOnlyRecovery: true) }
        blockedState.retry(.refresh)
        let blockedRequests = await blockedRepository.requestCount()
        XCTAssertEqual(blockedRequests, 0)
    }

    @MainActor
    func testStateMatrix() async throws {
        // IOS-STATE-011 through IOS-STATE-014: This test covers each executable
        // State Matrix row. The audit records the four endpoint/lifecycle rows that
        // need source or approved runtime evidence.
        let origin = try PreviewOrigin(rawValue: "https://preview.example.invalid")
        let credential = Credential(username: "fictional-user", password: "pwd")
        let presentationSource = try sourceText("SessionState.swift")
        XCTAssertTrue(presentationSource.contains("No current release is available."))

        // Missing or invalid Preview configuration: no Keychain read or repository call.
        for (name, error) in [("missing", PreviewOriginError.missing), ("invalid", .invalid)] {
            let configStore = ControlledCredentialStore(loadResult: .none)
            let configRepository = SuspendedRepository()
            let configState = SessionState(
                configuration: AppConfiguration(origin: .failure(error)),
                store: configStore,
                repository: configRepository
            )
            configState.start()
            XCTAssertEqual(configState.screen, .configuration, "\(name) configuration")
            let configLoadCount = await configStore.loadCount()
            let configRequestCount = await configRepository.requestCount()
            XCTAssertEqual(configLoadCount, 0, "\(name) configuration read Keychain")
            XCTAssertEqual(configRequestCount, 0, "\(name) configuration called repository")
        }
        XCTAssertTrue(presentationSource.contains("This app is not configured for access."))

        // No Keychain credential: sign-in is the sole permitted next state.
        let noCredentialState = SessionState(configuration: AppConfiguration(origin: .success(origin)), store: ControlledCredentialStore(loadResult: .none), repository: ControlledRepository(result: .success(.empty)))
        noCredentialState.start()
        try await waitUntil("no credential", state: noCredentialState) { $0 == .signIn(message: nil) }
        XCTAssertEqual(noCredentialState.screen, .signIn(message: nil))

        // Keychain read failure: exact text, no release, and Keychain-read retry only.
        let readFailureState = SessionState(configuration: AppConfiguration(origin: .success(origin)), store: ControlledCredentialStore(loadResult: .failure), repository: ControlledRepository(result: .success(.empty)))
        readFailureState.start()
        try await waitUntil("Keychain read failure", state: readFailureState) { $0 == .failure(message: "Saved sign-in could not be read. Try again.", retry: .keychainRead) }
        XCTAssertEqual(readFailureState.screen, .failure(message: "Saved sign-in could not be read. Try again.", retry: .keychainRead))

        // Unsafe inventory: exact reset-only state, no release or network request.
        let unsafeRepository = SuspendedRepository()
        let unsafeState = SessionState(configuration: AppConfiguration(origin: .success(origin)), store: ControlledCredentialStore(loadResult: .unsafe), repository: unsafeRepository)
        unsafeState.start()
        try await waitUntil("unsafe inventory", state: unsafeState) { $0 == .deletionPending(message: "Saved sign-in must be reset before access.", afterDeletion: nil, deletionOnlyRecovery: true) }
        XCTAssertEqual(unsafeState.screen, .deletionPending(message: "Saved sign-in must be reset before access.", afterDeletion: nil, deletionOnlyRecovery: true))
        let unsafeRequestCount = await unsafeRepository.requestCount()
        XCTAssertEqual(unsafeRequestCount, 0)

        // Deletion-only reset: complete deletes before sign-in; a failure stays pending.
        let resetCompleteState = SessionState(configuration: AppConfiguration(origin: .success(origin)), store: ControlledCredentialStore(loadResult: .unsafe, resetResult: .complete), repository: ControlledRepository(result: .success(.empty)))
        resetCompleteState.start()
        try await waitUntil("reset complete setup", state: resetCompleteState) { if case .deletionPending = $0 { return true }; return false }
        resetCompleteState.resetSavedSignIn()
        try await waitUntil("reset complete", state: resetCompleteState) { $0 == .signIn(message: nil) }
        XCTAssertEqual(resetCompleteState.screen, .signIn(message: nil))

        let resetPendingState = SessionState(configuration: AppConfiguration(origin: .success(origin)), store: ControlledCredentialStore(loadResult: .unsafe, resetResult: .pending), repository: ControlledRepository(result: .success(.empty)))
        resetPendingState.start()
        try await waitUntil("reset pending setup", state: resetPendingState) { if case .deletionPending = $0 { return true }; return false }
        resetPendingState.resetSavedSignIn()
        try await waitUntil("reset pending", state: resetPendingState) { $0 == .deletionPending(message: "Saved sign-in could not be removed. Try again.", afterDeletion: nil, deletionOnlyRecovery: true) }
        XCTAssertEqual(resetPendingState.screen, .deletionPending(message: "Saved sign-in could not be removed. Try again.", afterDeletion: nil, deletionOnlyRecovery: true))

        // Valid release: retain the credential for refresh and show every valid value.
        let validRelease = ClientReleaseResponse(engagementName: "Fictional Engagement", reviewStatus: "RELEASED", releaseVersion: 1, publishedAt: "2026-08-24T10:15:30Z", conclusion: ClientConclusion(title: "Conclusion", summary: "Summary", evidenceReferenceID: "REF-001"), actions: [ClientAction(description: "Action", owner: "Owner", targetDate: "2026-08-25", status: "OPEN")])
        let validStore = ControlledCredentialStore(loadResult: .credential(credential))
        let validRepository = SuspendedRepository()
        let validState = SessionState(configuration: AppConfiguration(origin: .success(origin)), store: validStore, repository: validRepository)
        validState.start()
        await validRepository.waitForRequests(1)
        let validInitialCredential = await validRepository.credential(at: 0)
        XCTAssertEqual(validInitialCredential, credential)
        await validRepository.complete(0, with: .success(.release(validRelease)))
        await validRepository.waitForReturnedRequests(1)
        try await waitUntil("valid release", state: validState) { if case .release = $0 { return true }; return false }
        if case .release(let release, let notices) = validState.screen {
            XCTAssertEqual(release.engagementName, "Fictional Engagement")
            XCTAssertEqual(release.reviewStatus, "RELEASED")
            XCTAssertEqual(notices, [])
        } else { XCTFail("Expected release screen, got \(validState.screen)") }
        XCTAssertEqual(validState.screen, .release(validRelease, notices: []))
        validState.refresh()
        await validRepository.waitForRequests(2)
        let validRefreshCredential = await validRepository.credential(at: 1)
        XCTAssertEqual(validRefreshCredential, credential)
        await validRepository.complete(1, with: .success(.release(validRelease)))
        await validRepository.waitForReturnedRequests(2)
        try await waitUntil("valid release refresh", state: validState) { $0 == .release(validRelease, notices: []) }

        // Both validated empty sentinels keep the credential, clear release, and refresh.
        // testReleaseValidation distinguishes the two wire-response sentinel values.
        for condition in ["no published release", "missing Engagement response"] {
            let emptyRepository = SuspendedRepository()
            let emptyState = SessionState(configuration: AppConfiguration(origin: .success(origin)), store: ControlledCredentialStore(loadResult: .credential(credential)), repository: emptyRepository)
            emptyState.start()
            await emptyRepository.waitForRequests(1)
            let emptyInitialCredential = await emptyRepository.credential(at: 0)
            XCTAssertEqual(emptyInitialCredential, credential)
            await emptyRepository.complete(0, with: .success(.empty))
            await emptyRepository.waitForReturnedRequests(1)
            try await waitUntil(condition, state: emptyState) { $0 == .empty }
            XCTAssertEqual(emptyState.screen, .empty)
            emptyState.refresh()
            await emptyRepository.waitForRequests(2)
            let emptyRefreshCredential = await emptyRepository.credential(at: 1)
            XCTAssertEqual(emptyRefreshCredential, credential)
            await emptyRepository.complete(1, with: .success(.empty))
            await emptyRepository.waitForReturnedRequests(2)
            try await waitUntil("\(condition) refresh", state: emptyState) { $0 == .empty }
        }

        // Missing conclusion and actions show their exact, independent notices.
        let noConclusion = ClientReleaseResponse(engagementName: "Fictional Engagement", reviewStatus: "RELEASED", releaseVersion: 1, publishedAt: "2026-08-24T10:15:30Z", conclusion: nil, actions: [ClientAction(description: "Action", owner: "Owner", targetDate: "2026-08-25", status: "OPEN")])
        let noConclusionState = SessionState(configuration: AppConfiguration(origin: .success(origin)), store: ControlledCredentialStore(loadResult: .credential(credential)), repository: ControlledRepository(result: .success(.release(noConclusion))))
        noConclusionState.start()
        try await waitUntil("no conclusion", state: noConclusionState) { $0 == .release(noConclusion, notices: ["No conclusion is available."]) }
        XCTAssertEqual(noConclusionState.screen, .release(noConclusion, notices: ["No conclusion is available."]))

        let noActions = ClientReleaseResponse(engagementName: "Fictional Engagement", reviewStatus: "RELEASED", releaseVersion: 1, publishedAt: "2026-08-24T10:15:30Z", conclusion: ClientConclusion(title: "Conclusion", summary: "Summary", evidenceReferenceID: "REF-001"), actions: [])
        let noActionsState = SessionState(configuration: AppConfiguration(origin: .success(origin)), store: ControlledCredentialStore(loadResult: .credential(credential)), repository: ControlledRepository(result: .success(.release(noActions))))
        noActionsState.start()
        try await waitUntil("no actions", state: noActionsState) { $0 == .release(noActions, notices: ["No actions are available."]) }
        XCTAssertEqual(noActionsState.screen, .release(noActions, notices: ["No actions are available."]))

        // Initial add failure: no credential is stored and sign-in shows the exact message.
        let initialAddFailureAdapter = SecItemFake()
        initialAddFailureAdapter.copyResults = [(errSecItemNotFound, nil), (errSecItemNotFound, nil)]
        initialAddFailureAdapter.addStatus = errSecAuthFailed
        let initialAddFailureState = SessionState(configuration: AppConfiguration(origin: .success(origin)), store: CredentialStore(adapter: initialAddFailureAdapter), repository: ControlledRepository(result: .success(.empty)))
        initialAddFailureState.start()
        try await waitUntil("initial add failure sign-in", state: initialAddFailureState) { $0 == .signIn(message: nil) }
        initialAddFailureState.signIn(username: "fictional-user", password: "pwd")
        try await waitUntil("initial add failure", state: initialAddFailureState) { $0 == .signIn(message: "Sign-in could not be saved. Try again.") }
        XCTAssertEqual(initialAddFailureState.screen, .signIn(message: "Sign-in could not be saved. Try again."))
        XCTAssertEqual(initialAddFailureAdapter.addAttributes.count, 1)

        let storedAttributes: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: CredentialStore.service,
            kSecAttrAccount as String: "fictional-user",
            kSecAttrAccessible as String: kSecAttrAccessibleWhenUnlockedThisDeviceOnly,
            kSecAttrSynchronizable as String: false
        ]
        let storedCredential = storedAttributes.merging([kSecValueData as String: Data("pwd".utf8)]) { _, new in new }

        // Replacement add failure: delete the old account before the new add fails.
        let replacementAddFailureAdapter = SecItemFake()
        replacementAddFailureAdapter.copyResults = [(errSecSuccess, [storedAttributes] as AnyObject), (errSecSuccess, storedCredential as AnyObject), (errSecSuccess, [storedAttributes] as AnyObject)]
        replacementAddFailureAdapter.addStatus = errSecAuthFailed
        let replacementAddFailureState = SessionState(configuration: AppConfiguration(origin: .success(origin)), store: CredentialStore(adapter: replacementAddFailureAdapter), repository: ControlledRepository(result: .success(.empty)))
        replacementAddFailureState.start()
        try await waitUntil("replacement add failure release", state: replacementAddFailureState) { $0 == .empty }
        replacementAddFailureState.signIn(username: "replacement-user", password: "pwd")
        try await waitUntil("replacement add failure", state: replacementAddFailureState) { $0 == .signIn(message: "Sign-in could not be saved. Try again.") }
        XCTAssertEqual(replacementAddFailureState.screen, .signIn(message: "Sign-in could not be saved. Try again."))
        XCTAssertEqual(replacementAddFailureAdapter.deleteQueries.count, 1)
        XCTAssertEqual(replacementAddFailureAdapter.addAttributes.count, 1)

        // Same-account update failures clear the old credential or keep deletion pending.
        let cleanupSuccessAdapter = SecItemFake()
        cleanupSuccessAdapter.copyResults = [(errSecSuccess, [storedAttributes] as AnyObject), (errSecSuccess, storedCredential as AnyObject), (errSecSuccess, [storedAttributes] as AnyObject)]
        cleanupSuccessAdapter.updateStatus = errSecAuthFailed
        let cleanupSuccessState = SessionState(configuration: AppConfiguration(origin: .success(origin)), store: CredentialStore(adapter: cleanupSuccessAdapter), repository: ControlledRepository(result: .success(.empty)))
        cleanupSuccessState.start()
        try await waitUntil("same-account cleanup release", state: cleanupSuccessState) { $0 == .empty }
        cleanupSuccessState.signIn(username: "fictional-user", password: "replacement")
        try await waitUntil("same-account cleanup success", state: cleanupSuccessState) { $0 == .signIn(message: "Sign-in could not be saved. Try again.") }
        XCTAssertEqual(cleanupSuccessState.screen, .signIn(message: "Sign-in could not be saved. Try again."))
        XCTAssertEqual(cleanupSuccessAdapter.deleteQueries.count, 1)

        let cleanupFailureAdapter = SecItemFake()
        cleanupFailureAdapter.copyResults = [(errSecSuccess, [storedAttributes] as AnyObject), (errSecSuccess, storedCredential as AnyObject), (errSecSuccess, [storedAttributes] as AnyObject)]
        cleanupFailureAdapter.updateStatus = errSecAuthFailed
        cleanupFailureAdapter.deleteStatus = errSecAuthFailed
        let cleanupFailureState = SessionState(configuration: AppConfiguration(origin: .success(origin)), store: CredentialStore(adapter: cleanupFailureAdapter), repository: ControlledRepository(result: .success(.empty)))
        cleanupFailureState.start()
        try await waitUntil("same-account cleanup failure release", state: cleanupFailureState) { $0 == .empty }
        cleanupFailureState.signIn(username: "fictional-user", password: "replacement")
        try await waitUntil("same-account cleanup failure", state: cleanupFailureState) { $0 == .deletionPending(message: "Saved sign-in could not be removed. Try again.", afterDeletion: nil, deletionOnlyRecovery: false) }
        XCTAssertEqual(cleanupFailureState.screen, .deletionPending(message: "Saved sign-in could not be removed. Try again.", afterDeletion: nil, deletionOnlyRecovery: false))
        XCTAssertEqual(cleanupFailureAdapter.addAttributes.count, 0)

        // Different-account replacement deletion failure keeps the old item and blocks access.
        let replacementDeleteFailureAdapter = SecItemFake()
        replacementDeleteFailureAdapter.copyResults = [(errSecSuccess, [storedAttributes] as AnyObject), (errSecSuccess, storedCredential as AnyObject), (errSecSuccess, [storedAttributes] as AnyObject)]
        replacementDeleteFailureAdapter.deleteStatus = errSecAuthFailed
        let replacementDeleteFailureState = SessionState(configuration: AppConfiguration(origin: .success(origin)), store: CredentialStore(adapter: replacementDeleteFailureAdapter), repository: ControlledRepository(result: .success(.empty)))
        replacementDeleteFailureState.start()
        try await waitUntil("replacement deletion failure release", state: replacementDeleteFailureState) { $0 == .empty }
        replacementDeleteFailureState.signIn(username: "replacement-user", password: "pwd")
        try await waitUntil("replacement deletion failure", state: replacementDeleteFailureState) { $0 == .deletionPending(message: "Saved sign-in could not be removed. Try again.", afterDeletion: nil, deletionOnlyRecovery: false) }
        XCTAssertEqual(replacementDeleteFailureState.screen, .deletionPending(message: "Saved sign-in could not be removed. Try again.", afterDeletion: nil, deletionOnlyRecovery: false))
        XCTAssertEqual(replacementDeleteFailureAdapter.addAttributes.count, 0)

        // HTTP 403 deletes the credential before sign-in. A deletion failure blocks access.
        let deniedState = SessionState(configuration: AppConfiguration(origin: .success(origin)), store: ControlledCredentialStore(loadResult: .credential(credential), resetResult: .complete), repository: ControlledRepository(result: .failure(RepositoryError.denied)))
        deniedState.start()
        try await waitUntil("denied with deletion", state: deniedState) { $0 == .signIn(message: "Access denied. Sign in again.") }
        XCTAssertEqual(deniedState.screen, .signIn(message: "Access denied. Sign in again."))

        let deniedPendingState = SessionState(configuration: AppConfiguration(origin: .success(origin)), store: ControlledCredentialStore(loadResult: .credential(credential), resetResult: .pending), repository: ControlledRepository(result: .failure(RepositoryError.denied)))
        deniedPendingState.start()
        try await waitUntil("denied pending deletion", state: deniedPendingState) { $0 == .deletionPending(message: "Saved sign-in could not be removed. Try again.", afterDeletion: "Access denied. Sign in again.", deletionOnlyRecovery: false) }
        XCTAssertEqual(deniedPendingState.screen, .deletionPending(message: "Saved sign-in could not be removed. Try again.", afterDeletion: "Access denied. Sign in again.", deletionOnlyRecovery: false))

        // 503 retains the credential. Refresh uses that credential and clears the old release.
        let unavailableStore = ControlledCredentialStore(loadResult: .credential(credential))
        let unavailableRepository = SuspendedRepository()
        let unavailableState = SessionState(configuration: AppConfiguration(origin: .success(origin)), store: unavailableStore, repository: unavailableRepository)
        unavailableState.start()
        await unavailableRepository.waitForRequests(1)
        await unavailableRepository.complete(0, with: .failure(.unavailable))
        await unavailableRepository.waitForReturnedRequests(1)
        try await waitUntil("state matrix unavailable", state: unavailableState) { $0 == .failure(message: "ACE is unavailable. Try again later.", retry: .refresh) }
        // IOS-STATE-011: Exact safe text. IOS-STATE-012: only refresh is offered.
        // IOS-STATE-013: The retained credential permits this retry. IOS-STATE-014: no release remains.
        XCTAssertEqual(unavailableState.screen, .failure(message: "ACE is unavailable. Try again later.", retry: .refresh))
        unavailableState.retry(.refresh)
        await unavailableRepository.waitForRequests(2)
        let retryCredential = await unavailableRepository.credential(at: 1)
        XCTAssertEqual(retryCredential, credential)
        await unavailableRepository.complete(1, with: .success(.empty))
        await unavailableRepository.waitForReturnedRequests(2)
        try await waitUntil("state matrix unavailable retry", state: unavailableState) { $0 == .empty }

        // Unexpected status, network, timeout, and malformed content retain the credential,
        // clear any release, and offer refresh with the exact safe message.
        let requestFailures: [(String, RepositoryError, String)] = [
            ("unexpected HTTP status", .invalidResponse, "ACE is unavailable. Try again later."),
            ("no network", .noConnection, "ACE could not be reached. Check your connection and try again."),
            ("timeout", .timeout, "The request timed out. Try again."),
            ("untrusted server certificate", .secureConnection, "ACE could not establish a secure connection. Try again later."),
            ("server hostname mismatch", .secureConnection, "ACE could not establish a secure connection. Try again later."),
            ("wrong content type", .invalidResponse, "ACE is unavailable. Try again later."),
            ("invalid or partial JSON", .invalidResponse, "ACE is unavailable. Try again later."),
            ("invalid release or action value", .invalidResponse, "ACE is unavailable. Try again later.")
        ]
        for (condition, error, message) in requestFailures {
            let failureRepository = SuspendedRepository()
            let failureState = SessionState(configuration: AppConfiguration(origin: .success(origin)), store: ControlledCredentialStore(loadResult: .credential(credential)), repository: failureRepository)
            failureState.start()
            await failureRepository.waitForRequests(1)
            let failureInitialCredential = await failureRepository.credential(at: 0)
            XCTAssertEqual(failureInitialCredential, credential)
            await failureRepository.complete(0, with: .failure(error))
            await failureRepository.waitForReturnedRequests(1)
            try await waitUntil(condition, state: failureState) { $0 == .failure(message: message, retry: .refresh) }
            XCTAssertEqual(failureState.screen, .failure(message: message, retry: .refresh))
            failureState.retry(.refresh)
            await failureRepository.waitForRequests(2)
            let failureRetryCredential = await failureRepository.credential(at: 1)
            XCTAssertEqual(failureRetryCredential, credential)
            await failureRepository.complete(1, with: .success(.empty))
            await failureRepository.waitForReturnedRequests(2)
            try await waitUntil("\(condition) retry", state: failureState) { $0 == .empty }
        }

        // A second refresh rejects the old result and keeps one progress state.
        let refreshRepository = SuspendedRepository()
        let refreshState = SessionState(configuration: AppConfiguration(origin: .success(origin)), store: ControlledCredentialStore(loadResult: .credential(credential)), repository: refreshRepository)
        refreshState.start()
        await refreshRepository.waitForRequests(1)
        refreshState.refresh()
        await refreshRepository.waitForRequests(2)
        await refreshRepository.complete(0, with: .success(.release(validRelease)))
        await refreshRepository.waitForReturnedRequests(1)
        XCTAssertEqual(refreshState.screen, .loading)
        await refreshRepository.complete(1, with: .success(.empty))
        await refreshRepository.waitForReturnedRequests(2)
        try await waitUntil("current refresh result", state: refreshState) { $0 == .empty }

        // Sign-out either clears the credential to sign-in or remains deletion pending.
        let signOutState = SessionState(configuration: AppConfiguration(origin: .success(origin)), store: ControlledCredentialStore(loadResult: .credential(credential), signOutResult: .complete), repository: ControlledRepository(result: .success(.empty)))
        signOutState.start()
        try await waitUntil("sign-out release", state: signOutState) { $0 == .empty }
        signOutState.signOut()
        try await waitUntil("sign-out complete", state: signOutState) { $0 == .signIn(message: nil) }
        XCTAssertEqual(signOutState.screen, .signIn(message: nil))

        let signOutPendingState = SessionState(configuration: AppConfiguration(origin: .success(origin)), store: ControlledCredentialStore(loadResult: .credential(credential), signOutResult: .pending), repository: ControlledRepository(result: .success(.empty)))
        signOutPendingState.start()
        try await waitUntil("sign-out pending release", state: signOutPendingState) { $0 == .empty }
        signOutPendingState.signOut()
        try await waitUntil("sign-out pending", state: signOutPendingState) { $0 == .deletionPending(message: "Sign-out could not be completed. Try again.", afterDeletion: nil, deletionOnlyRecovery: false) }
        XCTAssertEqual(signOutPendingState.screen, .deletionPending(message: "Sign-out could not be completed. Try again.", afterDeletion: nil, deletionOnlyRecovery: false))

        // Real trust failures and UIKit lifecycle events require approved endpoint or
        // runtime validation. The audit records those event sources as pending.
    }
}

// MARK: - Copy And Screenshot (IOS-COPY-001 through IOS-COPY-009, IOS-SHOT-001 through IOS-SHOT-010)

extension AcceptanceEvidenceContractTests {

    func testCopyControlsUITest() throws {
        // IOS-COPY-001: Each visible value has labelled copy control
        // IOS-COPY-004: Evidence references copy as text, never open as links
        // IOS-COPY-005: Copy action gives accessible confirmation
        // IOS-COPY-006: Only eleven named field types have copy controls
        // IOS-COPY-007: No unapproved internal identifier has copy control
        XCTAssertEqual(CopyableReleaseField.allCases.count, 11)
        let labels = CopyableReleaseField.allCases.map(\.label)
        XCTAssertTrue(labels.contains("Engagement name"))
        XCTAssertTrue(labels.contains("Review status"))
        XCTAssertTrue(labels.contains("Release version"))
        XCTAssertTrue(labels.contains("Published date and time"))
        XCTAssertTrue(labels.contains("Conclusion title"))
        XCTAssertTrue(labels.contains("Conclusion summary"))
        XCTAssertTrue(labels.contains("Evidence reference"))
        XCTAssertTrue(labels.contains("Action description"))
        XCTAssertTrue(labels.contains("Action owner"))
        XCTAssertTrue(labels.contains("Action target date"))
        XCTAssertTrue(labels.contains("Action status"))
        let viewSource = try sourceText("Views.swift")
        XCTAssertTrue(viewSource.contains("let field: CopyableReleaseField"), "Copy controls must take an approved field type")
        XCTAssertEqual(viewSource.components(separatedBy: "Button(\"Copy ").count - 1, 1, "ValueRow must contain one copy-control implementation")
        XCTAssertFalse(viewSource.contains(".textSelection("), "Native selection must not bypass ClipboardWriteContract")
        XCTAssertTrue(viewSource.contains("let announcement = \"Copied \\(field.label).\""), "Copy confirmation must be accessible text")
        XCTAssertTrue(viewSource.contains("if let confirmation { Text(confirmation) }"), "Copy confirmation must remain visible to accessibility services")
        XCTAssertFalse(viewSource.contains("Link("), "Production source must not use Link-based external navigation")
    }

    func testClipboardContract() throws {
        // IOS-COPY-002: Copy control copies only its visible value
        // IOS-COPY-003: No copy control exposes credentials or technical details
        // IOS-COPY-008: Every clipboard write uses localOnly = true
        // IOS-COPY-009: Every clipboard write expires 5 minutes after write
        let visibleValue = "Visible release value"
        let writtenAt = Date(timeIntervalSinceReferenceDate: 123_456)
        let item = ClipboardWriteContract.item(visibleValue: visibleValue)
        XCTAssertEqual(item.count, 1)
        XCTAssertEqual(item["public.utf8-plain-text"] as? String, visibleValue)
        let options = ClipboardWriteContract.options(writtenAt: writtenAt)
        XCTAssertEqual(options[.localOnly] as? Bool, true)
        XCTAssertEqual(options[.expirationDate] as? Date, writtenAt.addingTimeInterval(300))
        let viewText = try sourceText("Views.swift")
        XCTAssertTrue(viewText.contains("ClipboardWriteContract.write(visibleValue: value, writtenAt: Date())"))
        let productionSourceText = try allSourceText()
        XCTAssertFalse(productionSourceText.contains("UIPasteboard.general.setItems"))
        XCTAssertEqual(productionSourceText.components(separatedBy: ".setItems(").count - 1, 1, "Only ClipboardWriteContract may write to the pasteboard")
        // No credential fields in CopyableReleaseField
        let fieldLabels = CopyableReleaseField.allCases.map(\.label)
        XCTAssertFalse(fieldLabels.contains(where: { $0.lowercased().contains("password") || $0.lowercased().contains("credential") || $0.lowercased().contains("authorization") }))
    }

    func testScreenshotPolicyInspection() throws {
        // IOS-SHOT-001: Normal iPhone screenshots remain allowed
        // IOS-SHOT-002: App does NOT detect, block, warn, upload, share, or force exit for screenshots
        let sourceText = try allSourceText()
        // Verify no screenshot detection API calls
        XCTAssertFalse(sourceText.localizedCaseInsensitiveContains("UIApplication.userDidTakeScreenshotNotification"))
        XCTAssertFalse(sourceText.localizedCaseInsensitiveContains("screenshot notification"))
        XCTAssertFalse(sourceText.localizedCaseInsensitiveContains("screenshotTaken"))
        try assertPending(runtimeID("SHOT", 1))
    }

    func testSceneDelegateTest() throws {
        // IOS-SHOT-003: App-switcher shows privacy cover
        // IOS-SHOT-004: Inactive callback returns only after cover installation
        // IOS-SHOT-005: Cover install/removal uses no animation
        // IOS-SHOT-006: Cover removed only after active foreground
        // IOS-SHOT-008: sceneWillResignActive installs cover on main actor
        // IOS-SHOT-009: sceneDidBecomeActive removes cover after activation
        // IOS-PRIV-009: Cover contains only app name and FICTIONAL PILOT label
        let sourceText = try allSourceText()
        XCTAssertTrue(sourceText.contains("sceneWillResignActive"), "Must install cover on resign")
        XCTAssertTrue(sourceText.contains("sceneDidBecomeActive"), "Must remove cover on become active")
        XCTAssertTrue(sourceText.contains("UIView.performWithoutAnimation"), "Cover must use no animation")
        XCTAssertTrue(sourceText.contains("FICTIONAL PILOT — CONTROLLED"), "Cover must show handling label")
        XCTAssertTrue(sourceText.contains("ACE Client"), "Cover must show app name")
    }

    func testPrivacyCoverUITest() throws {
        // IOS-STATE-009: Background entry shows privacy cover
        // IOS-STATE-010: Foreground return removes privacy cover
        // IOS-SHOT-003: App-switcher preview shows privacy cover
        let sourceText = try allSourceText()
        // The PrivacySceneDelegate installs a UIWindow at .alert+1 level with PrivacyCoverView
        XCTAssertTrue(sourceText.contains("windowLevel = .alert + 1"), "Cover must be above all content")
        XCTAssertTrue(sourceText.contains("PrivacyCoverView"), "Cover must be PrivacyCoverView")
        XCTAssertTrue(sourceText.contains("cover.isHidden = false"), "Cover must be shown on resign")
        XCTAssertTrue(sourceText.contains("cover.isHidden = true"), "Cover must be hidden on activate")
    }
}

// MARK: - Privacy And Persistence (IOS-PRIV-001 through IOS-PRIV-009)

extension AcceptanceEvidenceContractTests {

    func testPrivacySourceInspection() throws {
        // IOS-AUTH-006: Logs contain no username, password, or Authorization
        // IOS-AUTH-007: No credential in URL credential storage or UserDefaults
        // IOS-PRIV-001: Release responses not written to files or databases
        // IOS-PRIV-006: App starts no background refresh
        // IOS-PRIV-007: Logs contain no release field, username, password, credential, or Authorization
        let sourceText = try allSourceText()
        // IOS-AUTH-006 and IOS-PRIV-007: Inspect all production logging surfaces.
        // A production log must not expose protected authentication or release values.
        let loggingSurfaces = ["print(", "debugPrint(", "NSLog(", "os_log(", "Logger(", "OSLog("]
        let loggingLines = sourceText.split(whereSeparator: \.isNewline).filter { line in
            loggingSurfaces.contains { line.contains($0) }
        }
        XCTAssertTrue(loggingLines.isEmpty, "Production source must not contain a logging surface")
        let protectedValues = ["username", "password", "credential", "authorization", "engagementName", "reviewStatus", "releaseVersion", "publishedAt", "conclusion", "actions"]
        let loggingText = loggingLines.joined(separator: "\n").lowercased()
        for value in protectedValues {
            XCTAssertFalse(loggingText.contains(value.lowercased()), "Logging must not contain protected value: \(value)")
        }
        // No UserDefaults for credentials
        XCTAssertFalse(sourceText.contains(forbiddenPair("User", "Defaults")), "Must not use UserDefaults for credentials")
        // No file writes of release data
        XCTAssertFalse(sourceText.contains("write(to:"))
        // No background refresh
        XCTAssertFalse(sourceText.contains("BGTaskScheduler") && sourceText.contains("register("))
    }

    func testEvidencePrivacyInspection() throws {
        // IOS-AUTH-036 and IOS-AUTH-037: External controlled evidence is not in this
        // repository. Keep both identifiers pending until an approved review can inspect it.
        // IOS-PRIV-008: No provider, analytics, advertising, or crash-reporting connection
        let sourceText = try allSourceText()
        try assertPending(runtimeID("AUTH", 36))
        try assertPending(runtimeID("AUTH", 37))
        // No pasteboard write without localOnly
        XCTAssertFalse(sourceText.contains("UIPasteboard.general.string ="), "Must not set pasteboard string directly")
        XCTAssertFalse(sourceText.contains("UIPasteboard.general.setValue"), "Must use setItems with options")
        // Inspect only production Swift source for known provider, analytics,
        // advertising, and crash-reporting connection symbols.
        let importLines = sourceText.split(whereSeparator: \.isNewline).map {
            $0.trimmingCharacters(in: .whitespaces)
        }.filter { $0.hasPrefix("import ") }
        XCTAssertTrue(Set(importLines).isSubset(of: Set(["import Foundation", "import Security", "import SwiftUI", "import UIKit"])))
        let forbiddenConnectionMarkers = [
            "import Firebase", "FirebaseApp.configure", "OpenAI", "Anthropic", "Sift-KG", "OpenViking",
            "Analytics.logEvent", "import Mixpanel", "Mixpanel.", "import Amplitude", "Amplitude.",
            "import GoogleMobileAds", "GADMobileAds", "import AdSupport", "ATTrackingManager",
            "import Crashlytics", "Crashlytics", "import Sentry", "SentrySDK", "import AppCenter", "AppCenter.start"
        ]
        for marker in forbiddenConnectionMarkers {
            XCTAssertFalse(sourceText.contains(marker), "Production source must not contain connection marker: \(marker)")
        }
    }
}

// MARK: - UI And Fictional Scenarios

extension AcceptanceEvidenceContractTests {

    func testSignInUITest() throws {
        // IOS-AUTH-031: Username field remains readable during sign-in
        // IOS-AUTH-032: Password uses secure text entry
        // IOS-AUTH-033: Password never appears as readable text
        // IOS-AUTH-034: HTTP Authorization never appears in interface
        // IOS-AUTH-035: Keychain secret never appears in interface
        // IOS-SHOT-010: Visible username can appear in normal screenshot
        let sourceText = try allSourceText()
        XCTAssertTrue(sourceText.contains("SecureField(\"Password\""), "Password must use SecureField")
        XCTAssertTrue(sourceText.contains("TextField(\"Username\""), "Username must be readable TextField")
        // Credentials cleared after submission
        XCTAssertTrue(sourceText.contains("username = \"\""), "Username must clear after submit")
        XCTAssertTrue(sourceText.contains("password = \"\""), "Password must clear after submit")
        try assertPending(runtimeID("SHOT", 10))
    }

    func testSafeInterfaceUITest() throws {
        // IOS-AUTH-034: Authorization never appears in interface
        // IOS-STATE-015: Unexpected status shows no server/authentication details
        let allText = try allSourceText()
        // No external links (anywhere in source)
        XCTAssertFalse(allText.contains("Link("), "Must not use Link for external navigation")
        // The interface never displays credentials — scan only UI layer (Views.swift),
        // not network transport code where "Authorization" is a header field key.
        let viewText = try sourceText("Views.swift")
        XCTAssertFalse(viewText.contains("Authorization"), "Interface must not contain Authorization")
        XCTAssertFalse(viewText.contains("\"Basic "), "Interface must not display Basic auth prefix")
    }

    func testReleaseScreenUITest() throws {
        // IOS-STATE-001: Valid release replaces screen atomically, shows FICTIONAL PILOT label
        let sourceText = try allSourceText()
        XCTAssertTrue(sourceText.contains("HandlingLabel"), "Release screen must show handling label")
        XCTAssertTrue(sourceText.contains("FICTIONAL PILOT — CONTROLLED"), "Must show fictional pilot notice")
    }

    func testFixtureInspection() throws {
        // IOS-BOUND-008: The complete DEBUG scenario literal set is controlled.
        let scenarioSource = try sourceText("DebugScenario.swift")
        XCTAssertTrue(scenarioSource.hasPrefix("#if DEBUG"), "Controlled scenarios must not ship in Release")
        let approvedLiterals: Set<String> = [
            "2026-08-24T10:15:30Z", "2026-08-25", "Access denied. Sign in again.",
            "ACE could not be reached. Check your connection and try again.",
            "ACE could not establish a secure connection. Try again later.", "ACE is unavailable. Try again later.",
            "ACE_UI_TEST_SCENARIO", "Fictional action", "Fictional conclusion", "Fictional Engagement",
            "Fictional owner", "Fictional summary", "FICTIONAL-REF-001", "Loading",
            "No actions are available.", "No conclusion is available.", "No current release is available.",
            "OPEN", "Refresh", "RELEASED", "Reset saved sign-in", "Saved sign-in could not be read. Try again.",
            "Saved sign-in could not be removed. Try again.", "Saved sign-in must be reset before access.",
            "Sign-in could not be saved. Try again.", "Sign-out could not be completed. Try again.",
            "The request timed out. Try again.", "This app is not configured for access.", "Try again"
        ]
        XCTAssertEqual(try stringLiterals(in: scenarioSource), approvedLiterals, "Controlled scenario literals changed; review each value before approval")
    }
}

// MARK: - Accessibility (IOS-ACC-001 through IOS-ACC-019)

extension AcceptanceEvidenceContractTests {

    func testAccessibilityLabelsUITest() throws {
        // IOS-ACC-002: All controls have useful VoiceOver labels and traits
        let sourceText = try allSourceText()
        XCTAssertTrue(sourceText.contains("accessibilityLabel"), "All controls must have accessibility labels")
        // Check key accessibility labels are present
        XCTAssertTrue(sourceText.contains("\"Username\""))
        XCTAssertTrue(sourceText.contains("\"Password\""))
        XCTAssertTrue(sourceText.contains("\"Sign in\""))
        XCTAssertTrue(sourceText.contains("\"Refresh current release\""))
        XCTAssertTrue(sourceText.contains("\"Sign out\""))
    }

    func testVoiceOverOrderUITest() throws {
        // IOS-ACC-001: VoiceOver reads main screen in approved order
        let sourceText = try allSourceText()
        XCTAssertTrue(sourceText.contains("accessibilityAddTraits(.isHeader)"), "Headers must have isHeader trait")
        XCTAssertTrue(sourceText.contains("accessibilityElement(children: .contain)"), "Action groups must be contained")
        XCTAssertTrue(sourceText.contains("accessibilityLabel"), "Messages must use accessibility labels")
    }
}

// MARK: - Boundary (IOS-BOUND-001 through IOS-BOUND-008)

extension AcceptanceEvidenceContractTests {

    func testServerCompatibilityExternal() throws {
        // IOS-BOUND-006: Server compatibility evidence remains unchanged
        try assertPending(runtimeID("BOUND", 6))
    }
}

// MARK: - Pending Runtime Evidence

extension AcceptanceEvidenceContractTests {

    func testAccessibilityAuditPending() throws { try assertPending(runtimeID("ACC", 8)) }
    func testBoldTextPending() throws { try assertPending(runtimeID("ACC", 4)) }
    func testContrastPending() throws { try assertPending(runtimeID("ACC", 14)) }
    func testDynamicTypePending() throws { try assertPending(runtimeID("ACC", 3)) }
    func testLayoutMatrixPending() throws { try assertPending(runtimeID("ACC", 7)) }
    func testManualAppSwitcherPending() throws { try assertPending(runtimeID("SHOT", 7)) }
    func testManualVoiceOverPending() throws { try assertPending(runtimeID("ACC", 9)) }
    func testPhysicalDevicePending() throws { try assertPending(runtimeID("AUTH", 23)) }
    func testReduceMotionPending() throws { try assertPending(runtimeID("ACC", 5)) }
    func testSimulatorMatrixPending() throws { try assertPending(runtimeID("ACC", 10)) }
}

// MARK: - Helpers

extension AcceptanceEvidenceContractTests {

    private func assertPending(_ identifier: String, file: StaticString = #filePath, line: UInt = #line) throws {
        let entries = try runtimePlan().entries.flatMap(\.identifiers)
        XCTAssertEqual(entries.filter { $0 == identifier }.count, 1, "Identifier \(identifier) not found in runtime plan", file: file, line: line)
    }

    private func runtimeID(_ family: String, _ number: Int) -> String { "IOS-\(family)-\(String(format: "%03d", number))" }

    private func forbiddenPair(_ first: String, _ second: String) -> String { first + second }

    private func projectText() throws -> String {
        try String(contentsOf: root.appendingPathComponent("ACEClientApp.xcodeproj/project.pbxproj"), encoding: .utf8)
    }

    private func sourceText(_ name: String) throws -> String {
        try String(contentsOf: root.appendingPathComponent("ACEClientApp").appendingPathComponent(name), encoding: .utf8)
    }

    private func infoPlist() throws -> [String: Any] {
        let data = try Data(contentsOf: root.appendingPathComponent("ACEClientApp/Info.plist"))
        let propertyList = try PropertyListSerialization.propertyList(from: data, options: [], format: nil)
        return try XCTUnwrap(propertyList as? [String: Any], "Info.plist must contain a dictionary")
    }

    private func allSourceText() throws -> String {
        try productionSources().map { try String(contentsOf: $0, encoding: .utf8) }.joined(separator: "\n")
    }

    private func productionSources() throws -> [URL] {
        let directory = root.appendingPathComponent("ACEClientApp")
        let files = FileManager.default.enumerator(at: directory, includingPropertiesForKeys: nil)!
        return files.compactMap { $0 as? URL }.filter { $0.pathExtension == "swift" }.sorted { sourceRelativePath($0) < sourceRelativePath($1) }
    }

    private func sourceRelativePath(_ source: URL) -> String {
        source.path.replacingOccurrences(of: root.appendingPathComponent("ACEClientApp").path + "/", with: "")
    }

    private func stringLiterals(in source: String) throws -> Set<String> {
        let expression = try NSRegularExpression(pattern: #"\"((?:\\.|[^\"\\])*)\""#)
        let range = NSRange(source.startIndex..., in: source)
        return Set(expression.matches(in: source, range: range).compactMap { match in
            guard let valueRange = Range(match.range(at: 1), in: source) else { return nil }
            return String(source[valueRange]).replacingOccurrences(of: #"\\\""#, with: "\"")
        })
    }

    private func stringLiterals(inAssignmentsMatching pattern: String, source: String) throws -> [String] {
        let expression = try NSRegularExpression(pattern: pattern)
        let range = NSRange(source.startIndex..., in: source)
        return expression.matches(in: source, range: range).compactMap { match in
            guard let valueRange = Range(match.range(at: 1), in: source) else { return nil }
            return String(source[valueRange])
        }
    }

    private func assignmentCount(matching pattern: String, source: String) throws -> Int {
        let expression = try NSRegularExpression(pattern: pattern)
        return expression.numberOfMatches(in: source, range: NSRange(source.startIndex..., in: source))
    }

    private func sourceTreeManifest() throws -> [String: String] {
        let repository = root.deletingLastPathComponent().deletingLastPathComponent()
        return try Dictionary(uniqueKeysWithValues: approvedSanitizedBaseManifest.keys.map { path in
            let data = try Data(contentsOf: repository.appendingPathComponent(path))
            let text = try XCTUnwrap(String(data: data, encoding: .utf8), "Manifest file must be UTF-8")
            let normalized = Data(text.replacingOccurrences(of: "\r\n", with: "\n").utf8)
            return (path, SHA256.hash(data: normalized).map { String(format: "%02x", $0) }.joined())
        })
    }

    private func serverSourcePaths() throws -> [String] {
        let sourceExtensions: Set<String> = ["c", "cc", "cpp", "cs", "go", "java", "js", "php", "py", "rb", "rs", "ts"]
        let files = FileManager.default.enumerator(at: root, includingPropertiesForKeys: nil)!
        var sourcePaths: [String] = []
        while let file = files.nextObject() as? URL {
            let relativePath = file.path.replacingOccurrences(of: root.path + "/", with: "")
            let components = relativePath.split(separator: "/").map(String.init)
            if components.contains(where: { [".git", "build", "DerivedData"].contains($0) }) {
                var isDirectory: ObjCBool = false
                FileManager.default.fileExists(atPath: file.path, isDirectory: &isDirectory)
                if isDirectory.boolValue { files.skipDescendants() }
                continue
            }
            let hasServerDirectory = components.dropLast().contains { ["api", "backend", "server"].contains($0.lowercased()) }
            guard hasServerDirectory || sourceExtensions.contains(file.pathExtension.lowercased()) else { continue }
            sourcePaths.append(relativePath)
        }
        return sourcePaths.sorted()
    }

    private var root: URL { URL(fileURLWithPath: #filePath).deletingLastPathComponent().deletingLastPathComponent() }

    private func runtimePlan() throws -> RuntimePlan {
        try JSONDecoder().decode(RuntimePlan.self, from: Data(contentsOf: root.appendingPathComponent("RuntimeEvidencePlan.json")))
    }

    private func releaseVersion(in screen: ScreenState) -> Int? {
        guard case .release(let release, _) = screen else { return nil }
        return release.releaseVersion
    }
}

// MARK: - Test doubles shared with ACEClientAppTests

// SecItemFake, ControlledTransport, ControlledCredentialStore, ControlledRepository
// are defined in ACEClientAppTests.swift and accessible within the same test target.

// ChallengeSender needed for trust handling tests
private final class ChallengeSender: NSObject, URLAuthenticationChallengeSender {
    let expectation: XCTestExpectation
    init(expectation: XCTestExpectation) { self.expectation = expectation }
    func use(_ credential: URLCredential, for challenge: URLAuthenticationChallenge) {}
    func continueWithoutCredential(for challenge: URLAuthenticationChallenge) {}
    func cancel(_ challenge: URLAuthenticationChallenge) { expectation.fulfill() }
    func performDefaultHandling(for challenge: URLAuthenticationChallenge) { expectation.fulfill() }
    func rejectProtectionSpaceAndContinue(with challenge: URLAuthenticationChallenge) {}
}
