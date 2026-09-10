import Combine
import Foundation
import XCTest
import Security
// Production sources compiled directly into test target — no @testable import needed.

final class ACEClientAppTests: XCTestCase {
    func testValidReleasePassesValidation() throws {
        let release = ClientReleaseResponse(
            engagementName: "Fictional Engagement", reviewStatus: "RELEASED", releaseVersion: 1,
            publishedAt: "2026-08-24T10:15:30Z", conclusion: nil, actions: []
        )
        XCTAssertEqual(try release.validated(), .release(release))
    }

    func testOnlyDefinedEmptyResponsePassesValidation() throws {
        let empty = ClientReleaseResponse(engagementName: "Release unavailable", reviewStatus: "", releaseVersion: 0, publishedAt: "", conclusion: nil, actions: [])
        XCTAssertEqual(try empty.validated(), .empty)
        let missingEngagement = ClientReleaseResponse(engagementName: "Engagement not found", reviewStatus: "", releaseVersion: 0, publishedAt: "", conclusion: nil, actions: [])
        XCTAssertEqual(try missingEngagement.validated(), .empty)
    }

    func testMissingTopLevelNestedAndActionsFieldsFailDecoding() throws {
        let decoder = JSONDecoder()
        XCTAssertThrowsError(try decoder.decode(ClientReleaseResponse.self, from: Data("{\"review_status\":\"RELEASED\"}".utf8)))
        XCTAssertThrowsError(try decoder.decode(ClientReleaseResponse.self, from: Data("{\"engagement_name\":\"Fictional\",\"review_status\":\"RELEASED\",\"release_version\":1,\"published_at\":\"2026-08-24T10:15:30Z\",\"conclusion\":{\"title\":\"Title\"},\"actions\":[]}".utf8)))
        XCTAssertThrowsError(try decoder.decode(ClientReleaseResponse.self, from: Data("{\"engagement_name\":\"Fictional\",\"review_status\":\"RELEASED\",\"release_version\":1,\"published_at\":\"2026-08-24T10:15:30Z\",\"conclusion\":null}".utf8)))
    }

    func testActionOrderAndUnknownFieldsRemainSafe() throws {
        let data = Data("{\"engagement_name\":\"Fictional\",\"review_status\":\"RELEASED\",\"release_version\":1,\"published_at\":\"2026-08-24T10:15:30Z\",\"conclusion\":null,\"actions\":[{\"description\":\"First\",\"owner\":\"Owner one\",\"target_date\":\"2026-08-25\",\"status\":\"OPEN\"},{\"description\":\"Second\",\"owner\":\"Owner two\",\"target_date\":\"2026-08-26\",\"status\":\"COMPLETE\"}],\"ignored\":true}".utf8)
        let release = try JSONDecoder().decode(ClientReleaseResponse.self, from: data)
        XCTAssertEqual(release.actions.map(\.description), ["First", "Second"])
        XCTAssertEqual(try release.validated(), .release(release))
    }

    func testInvalidReleaseValuesFailClosed() {
        let invalids = [
            ClientReleaseResponse(engagementName: "Fictional", reviewStatus: "RELEASED", releaseVersion: 0, publishedAt: "2026-08-24T10:15:30Z", conclusion: nil, actions: []),
            ClientReleaseResponse(engagementName: "Release unavailable", reviewStatus: "x", releaseVersion: 0, publishedAt: "", conclusion: nil, actions: []),
            ClientReleaseResponse(engagementName: "Fictional", reviewStatus: "RELEASED", releaseVersion: -1, publishedAt: "2026-02-30T10:15:30Z", conclusion: nil, actions: []),
            ClientReleaseResponse(engagementName: "Fictional", reviewStatus: "RELEASED", releaseVersion: 1, publishedAt: "2026-08-24T10:15:30Z", conclusion: nil, actions: [ClientAction(description: "Action", owner: "Owner", targetDate: "2026-02-30", status: "OTHER")])
        ]
        for release in invalids { XCTAssertThrowsError(try release.validated()) }
    }

    func testOriginRequiresAbsoluteHTTPSRoot() throws {
        XCTAssertThrowsError(try PreviewOrigin(rawValue: ""))
        XCTAssertThrowsError(try PreviewOrigin(rawValue: "http://example.invalid"))
        for invalidHost in [".preview.example.invalid", "preview..example.invalid", "preview_example.invalid"] {
            XCTAssertThrowsError(try PreviewOrigin(rawValue: "https://\(invalidHost)"), invalidHost)
        }
        XCTAssertNoThrow(try PreviewOrigin(rawValue: "https://preview.example.invalid"))
    }

    func testRequestIsGETAndHasNoCache() throws {
        let origin = try PreviewOrigin(rawValue: "https://preview.example.invalid")
        let request = try CurrentReleaseRequest.make(origin: origin, credential: Credential(username: "fictional-user", password: String(repeating: "x", count: 12)))
        XCTAssertEqual(request.httpMethod, "GET")
        XCTAssertEqual(request.cachePolicy, .reloadIgnoringLocalCacheData)
        XCTAssertEqual(request.url?.path, "/client/api/v1/release/current")
    }

    func testInventoryUsesAllSynchronisationClassesAndExactReadUsesFalse() async {
        let adapter = SecItemFake()
        let attributes: [String: Any] = [
            kSecAttrService as String: CredentialStore.service,
            kSecAttrAccount as String: "fictional-user",
            kSecAttrAccessible as String: kSecAttrAccessibleWhenUnlockedThisDeviceOnly,
            kSecAttrSynchronizable as String: false
        ]
        adapter.copyResults = [(errSecSuccess, [attributes] as AnyObject), (errSecSuccess, attributes.merging([kSecValueData as String: Data(repeating: 120, count: 12)]) { _, new in new } as AnyObject)]
        let store = CredentialStore(adapter: adapter)
        guard case .credential = await store.load() else { return XCTFail("Expected approved credential") }
        XCTAssertEqual(adapter.queries[0][kSecAttrSynchronizable as String] as? String, kSecAttrSynchronizableAny as String)
        XCTAssertEqual(adapter.queries[1][kSecAttrSynchronizable as String] as? Bool, false)
    }

    func testDeletionUsesServiceAndAllSynchronisationClasses() async {
        let adapter = SecItemFake()
        adapter.deleteStatus = errSecItemNotFound
        let store = CredentialStore(adapter: adapter)
        let result = await store.signOut()
        XCTAssertEqual(result, .complete)
        XCTAssertEqual(adapter.deleteQueries.count, 1)
        XCTAssertEqual(adapter.deleteQueries[0][kSecAttrService as String] as? String, CredentialStore.service)
        XCTAssertEqual(adapter.deleteQueries[0][kSecAttrSynchronizable as String] as? String, kSecAttrSynchronizableAny as String)
    }

    func testExactReadNotFoundAfterInventoryIsUnsafe() async {
        let adapter = SecItemFake()
        adapter.copyResults = [(errSecSuccess, [approvedAttributes()] as AnyObject), (errSecItemNotFound, nil)]
        let result = await CredentialStore(adapter: adapter).load()
        XCTAssertEqual(result, .unsafe)
    }

    func testExactReadFailureAfterInventoryIsControlledReadFailure() async {
        let adapter = SecItemFake()
        adapter.copyResults = [(errSecSuccess, [approvedAttributes()] as AnyObject), (errSecAuthFailed, nil)]
        let result = await CredentialStore(adapter: adapter).load()
        XCTAssertEqual(result, .failure)
    }

    func testInvalidReturnedAttributeEntersUnsafeRecovery() async {
        let adapter = SecItemFake()
        var invalid = approvedAttributes()
        invalid[kSecAttrSynchronizable as String] = true
        adapter.copyResults = [(errSecSuccess, [invalid] as AnyObject)]
        let result = await CredentialStore(adapter: adapter).load()
        XCTAssertEqual(result, .unsafe)
    }

    func testSaveAddsExactGenericPasswordContract() async {
        let adapter = SecItemFake()
        adapter.copyResults = [(errSecItemNotFound, nil)]
        let result = await CredentialStore(adapter: adapter).save(Credential(username: "fictional-user", password: String(repeating: "x", count: 12)))
        XCTAssertEqual(result, .saved)
        XCTAssertEqual(adapter.addAttributes.count, 1)
        let item = adapter.addAttributes[0]
        XCTAssertEqual(item[kSecClass as String] as? String, kSecClassGenericPassword as String)
        XCTAssertEqual(item[kSecAttrService as String] as? String, CredentialStore.service)
        XCTAssertEqual(item[kSecAttrAccount as String] as? String, "fictional-user")
        XCTAssertEqual(item[kSecAttrSynchronizable as String] as? Bool, false)
        XCTAssertNil(item[kSecAttrAccessGroup as String])
    }

    func testDuplicateAddUpdatesExactAccountOnly() async {
        let adapter = SecItemFake()
        adapter.copyResults = [(errSecItemNotFound, nil)]
        adapter.addStatus = errSecDuplicateItem
        let result = await CredentialStore(adapter: adapter).save(Credential(username: "fictional-user", password: String(repeating: "x", count: 12)))
        XCTAssertEqual(result, .saved)
        XCTAssertEqual(adapter.updateQueries.count, 1)
        XCTAssertEqual(adapter.updateQueries[0][kSecAttrAccount as String] as? String, "fictional-user")
        XCTAssertEqual(Set(adapter.updateAttributes[0].keys), Set([kSecValueData as String]))
    }

    func testSameAccountUpdateFailureDeletesAllServiceItems() async {
        let adapter = SecItemFake()
        adapter.copyResults = [(errSecSuccess, [approvedAttributes()] as AnyObject)]
        adapter.updateStatus = errSecAuthFailed
        adapter.deleteStatus = errSecSuccess
        let result = await CredentialStore(adapter: adapter).save(Credential(username: "fictional-user", password: String(repeating: "x", count: 12)))
        XCTAssertEqual(result, .saveFailure)
        XCTAssertEqual(adapter.deleteQueries[0][kSecAttrSynchronizable as String] as? String, kSecAttrSynchronizableAny as String)
    }

    func testDifferentAccountDeletesBeforeAddingReplacement() async {
        let adapter = SecItemFake()
        adapter.copyResults = [(errSecSuccess, [approvedAttributes()] as AnyObject)]
        adapter.deleteStatus = errSecSuccess
        let result = await CredentialStore(adapter: adapter).save(Credential(username: "fictional-new-user", password: String(repeating: "x", count: 12)))
        XCTAssertEqual(result, .saved)
        XCTAssertEqual(adapter.deleteQueries.count, 1)
        XCTAssertEqual(adapter.addAttributes[0][kSecAttrAccount as String] as? String, "fictional-new-user")
    }

    func testRepositoryMapsDeniedWithoutJSONContentType() async {
        let origin = try! PreviewOrigin(rawValue: "https://preview.example.invalid")
        let response = HTTPURLResponse(url: origin.url, statusCode: 403, httpVersion: nil, headerFields: ["Content-Type": "text/plain"])!
        let repository = HTTPCurrentReleaseRepository(origin: origin, transport: ControlledTransport(result: .success((Data(), response))))
        do {
            _ = try await repository.fetchCurrentRelease(credential: Credential(username: "fictional-user", password: String(repeating: "x", count: 12)))
            XCTFail("Expected denied result")
        } catch let error as RepositoryError { XCTAssertEqual(error, .denied) }
        catch { XCTFail("Unexpected result") }
    }

    func testRepositoryRejectsWrongSuccessContentType() async {
        let origin = try! PreviewOrigin(rawValue: "https://preview.example.invalid")
        let response = HTTPURLResponse(url: origin.url, statusCode: 200, httpVersion: nil, headerFields: ["Content-Type": "text/plain"])!
        let repository = HTTPCurrentReleaseRepository(origin: origin, transport: ControlledTransport(result: .success((Data(), response))))
        do {
            _ = try await repository.fetchCurrentRelease(credential: Credential(username: "fictional-user", password: String(repeating: "x", count: 12)))
            XCTFail("Expected invalid result")
        } catch let error as RepositoryError { XCTAssertEqual(error, .invalidResponse) }
        catch { XCTFail("Unexpected result") }
    }

    private func approvedAttributes() -> [String: Any] {
        [kSecAttrService as String: CredentialStore.service,
         kSecAttrAccount as String: "fictional-user",
         kSecAttrAccessible as String: kSecAttrAccessibleWhenUnlockedThisDeviceOnly,
         kSecAttrSynchronizable as String: false]
    }

    @MainActor
    func testStateUsesControlledStoreForNoCredentialAndUnsafeRecovery() async throws {
        let origin = try PreviewOrigin(rawValue: "https://preview.example.invalid")
        let repository = ControlledRepository(result: .failure(RepositoryError.unavailable))
        let noCredential = SessionState(configuration: AppConfiguration(origin: .success(origin)), store: ControlledCredentialStore(loadResult: .none), repository: repository)
        noCredential.start()
        try await waitUntil("no-credential sign-in", state: noCredential) { $0 == .signIn(message: nil) }
        XCTAssertEqual(noCredential.screen, .signIn(message: nil))
        let unsafe = SessionState(configuration: AppConfiguration(origin: .success(origin)), store: ControlledCredentialStore(loadResult: .unsafe), repository: repository)
        unsafe.start()
        try await waitUntil("unsafe saved sign-in", state: unsafe) { $0 == .deletionPending(message: "Saved sign-in must be reset before access.", afterDeletion: nil, deletionOnlyRecovery: true) }
        XCTAssertEqual(unsafe.screen, .deletionPending(message: "Saved sign-in must be reset before access.", afterDeletion: nil, deletionOnlyRecovery: true))
    }

    @MainActor
    func testStateMapsUnavailableAndSignOutDeletionFailure() async throws {
        let origin = try PreviewOrigin(rawValue: "https://preview.example.invalid")
        let credential = Credential(username: "fictional-user", password: String(repeating: "x", count: 12))
        let store = ControlledCredentialStore(loadResult: .credential(credential), signOutResult: .pending)
        let state = SessionState(configuration: AppConfiguration(origin: .success(origin)), store: store, repository: ControlledRepository(result: .failure(RepositoryError.unavailable)))
        state.start()
        try await waitUntil("unavailable response", state: state) { $0 == .failure(message: "ACE is unavailable. Try again later.", retry: .refresh) }
        XCTAssertEqual(state.screen, .failure(message: "ACE is unavailable. Try again later.", retry: .refresh))
        state.signOut()
        try await waitUntil("sign-out deletion failure", state: state) { $0 == .deletionPending(message: "Sign-out could not be completed. Try again.", afterDeletion: nil, deletionOnlyRecovery: false) }
        XCTAssertEqual(state.screen, .deletionPending(message: "Sign-out could not be completed. Try again.", afterDeletion: nil, deletionOnlyRecovery: false))
    }

}

final class SecItemFake: SecItemAdapter, @unchecked Sendable {
    private let lock = NSLock()
    private var copyResultsStorage: [(OSStatus, AnyObject?)] = []
    private var queriesStorage: [[String: Any]] = []
    private var deleteQueriesStorage: [[String: Any]] = []
    private var addStatusStorage: OSStatus = errSecSuccess
    private var updateStatusStorage: OSStatus = errSecSuccess
    private var deleteStatusStorage: OSStatus = errSecSuccess
    private var addAttributesStorage: [[String: Any]] = []
    private var updateQueriesStorage: [[String: Any]] = []
    private var updateAttributesStorage: [[String: Any]] = []

    var copyResults: [(OSStatus, AnyObject?)] { get { withLock { copyResultsStorage } } set { withLock { copyResultsStorage = newValue } } }
    var queries: [[String: Any]] { withLock { queriesStorage } }
    var deleteQueries: [[String: Any]] { withLock { deleteQueriesStorage } }
    var addStatus: OSStatus { get { withLock { addStatusStorage } } set { withLock { addStatusStorage = newValue } } }
    var updateStatus: OSStatus { get { withLock { updateStatusStorage } } set { withLock { updateStatusStorage = newValue } } }
    var deleteStatus: OSStatus { get { withLock { deleteStatusStorage } } set { withLock { deleteStatusStorage = newValue } } }
    var addAttributes: [[String: Any]] { withLock { addAttributesStorage } }
    var updateQueries: [[String: Any]] { withLock { updateQueriesStorage } }
    var updateAttributes: [[String: Any]] { withLock { updateAttributesStorage } }

    func copyMatching(_ query: [String: Any]) -> (OSStatus, AnyObject?) { withLock { queriesStorage.append(query); return copyResultsStorage.removeFirst() } }
    func add(_ attributes: [String: Any]) -> OSStatus { withLock { addAttributesStorage.append(attributes); return addStatusStorage } }
    func update(_ query: [String: Any], attributes: [String: Any]) -> OSStatus { withLock { updateQueriesStorage.append(query); updateAttributesStorage.append(attributes); return updateStatusStorage } }
    func delete(_ query: [String: Any]) -> OSStatus { withLock { deleteQueriesStorage.append(query); return deleteStatusStorage } }
    private func withLock<T>(_ body: () -> T) -> T { lock.lock(); defer { lock.unlock() }; return body() }
}

/// A stateful Keychain double. Use it when the final item inventory is evidence.
final class StatefulSecItemFake: SecItemAdapter, @unchecked Sendable {
    private let lock = NSLock()
    private var itemsStorage: [[String: Any]]
    private var deleteQueriesStorage: [[String: Any]] = []
    private var addAttributesStorage: [[String: Any]] = []

    init(items: [[String: Any]]) { self.itemsStorage = items }

    var items: [[String: Any]] { withLock { itemsStorage } }
    var deleteQueries: [[String: Any]] { withLock { deleteQueriesStorage } }
    var addAttributes: [[String: Any]] { withLock { addAttributesStorage } }

    func copyMatching(_ query: [String: Any]) -> (OSStatus, AnyObject?) {
        withLock {
            let matchedItems = itemsStorage.filter { item in matches(item, query: query) }
            guard !matchedItems.isEmpty else { return (errSecItemNotFound, nil) }
            if query[kSecAttrAccount as String] != nil {
                return (errSecSuccess, matchedItems[0] as AnyObject)
            }
            return (errSecSuccess, matchedItems.map { item in
                item.filter { $0.key != (kSecValueData as String) }
            } as AnyObject)
        }
    }

    func add(_ attributes: [String: Any]) -> OSStatus {
        withLock {
            addAttributesStorage.append(attributes)
            guard let account = attributes[kSecAttrAccount as String] as? String,
                  !itemsStorage.contains(where: { $0[kSecAttrAccount as String] as? String == account }) else {
                return errSecDuplicateItem
            }
            itemsStorage.append(attributes)
            return errSecSuccess
        }
    }

    func update(_ query: [String: Any], attributes: [String: Any]) -> OSStatus {
        withLock {
            guard let index = itemsStorage.firstIndex(where: { matches($0, query: query) }) else {
                return errSecItemNotFound
            }
            itemsStorage[index].merge(attributes) { _, new in new }
            return errSecSuccess
        }
    }

    func delete(_ query: [String: Any]) -> OSStatus {
        withLock {
            deleteQueriesStorage.append(query)
            let previousCount = itemsStorage.count
            itemsStorage.removeAll { matches($0, query: query) }
            return itemsStorage.count == previousCount ? errSecItemNotFound : errSecSuccess
        }
    }

    private func matches(_ item: [String: Any], query: [String: Any]) -> Bool {
        for key in [kSecClass as String, kSecAttrService as String, kSecAttrAccount as String] {
            guard let expected = query[key] else { continue }
            if let expected = expected as? String, item[key] as? String != expected { return false }
        }
        if let synchronisable = query[kSecAttrSynchronizable as String] as? Bool,
           item[kSecAttrSynchronizable as String] as? Bool != synchronisable { return false }
        return true
    }

    private func withLock<T>(_ body: () -> T) -> T { lock.lock(); defer { lock.unlock() }; return body() }
}

final class ConcurrentKeychainAdapter: SecItemAdapter, @unchecked Sendable {
    enum Operation: Equatable, Sendable {
        case copyMatching
        case add
        case update
        case delete
    }

    enum OperationEvent: Equatable, Sendable {
        case started(Operation)
        case completed(Operation)
    }

    private let stateLock = NSLock()
    private let activityLock = NSLock()
    private var account: String?
    private var password: Data?
    private var inFlight = 0
    private var maximumInFlight = 0
    private var operationEvents: [OperationEvent] = []
    struct Snapshot: Sendable { let itemCount: Int; let maximumInFlight: Int; let operationEvents: [OperationEvent] }
    func copyMatching(_ query: [String: Any]) -> (OSStatus, AnyObject?) { operation(.copyMatching) { stateLock.lock(); defer { stateLock.unlock() }; guard let account else { return (errSecItemNotFound, nil) }; let attributes = item(account: account); if let requested = query[kSecAttrAccount as String] as? String { guard requested == account, let password else { return (errSecItemNotFound, nil) }; return (errSecSuccess, attributes.merging([kSecValueData as String: password]) { _, new in new } as AnyObject) }; return (errSecSuccess, [attributes] as AnyObject) } }
    func add(_ attributes: [String: Any]) -> OSStatus { operation(.add) { stateLock.lock(); defer { stateLock.unlock() }; guard account == nil, let newAccount = attributes[kSecAttrAccount as String] as? String, let newPassword = attributes[kSecValueData as String] as? Data else { return errSecDuplicateItem }; account = newAccount; password = newPassword; return errSecSuccess } }
    func update(_ query: [String: Any], attributes: [String: Any]) -> OSStatus { operation(.update) { stateLock.lock(); defer { stateLock.unlock() }; guard query[kSecAttrAccount as String] as? String == account, let newPassword = attributes[kSecValueData as String] as? Data else { return errSecItemNotFound }; password = newPassword; return errSecSuccess } }
    func delete(_ query: [String: Any]) -> OSStatus { operation(.delete) { stateLock.lock(); defer { stateLock.unlock() }; let hadItem = account != nil; account = nil; password = nil; return hadItem ? errSecSuccess : errSecItemNotFound } }
    func snapshot() -> Snapshot { stateLock.lock(); let itemCount = account == nil ? 0 : 1; stateLock.unlock(); activityLock.lock(); let maximum = maximumInFlight; let events = operationEvents; activityLock.unlock(); return Snapshot(itemCount: itemCount, maximumInFlight: maximum, operationEvents: events) }
    private func item(account: String) -> [String: Any] { [kSecAttrService as String: CredentialStore.service, kSecAttrAccount as String: account, kSecAttrAccessible as String: kSecAttrAccessibleWhenUnlockedThisDeviceOnly, kSecAttrSynchronizable as String: false] }
    private func operation<T>(_ operation: Operation, _ body: () -> T) -> T { activityLock.lock(); inFlight += 1; maximumInFlight = max(maximumInFlight, inFlight); operationEvents.append(.started(operation)); activityLock.unlock(); defer { activityLock.lock(); inFlight -= 1; operationEvents.append(.completed(operation)); activityLock.unlock() }; return body() }
}

final class ControlledTransport: CurrentReleaseTransport, @unchecked Sendable {
    let result: Result<(Data, HTTPURLResponse), Error>
    private let lock = NSLock()
    private var calls = 0
    init(result: Result<(Data, HTTPURLResponse), Error>) { self.result = result }
    func fetchCurrentRelease(request: URLRequest) async throws -> (Data, HTTPURLResponse) {
        lock.withLock { calls += 1 }
        return try result.get()
    }
    func requestCount() -> Int {
        lock.withLock { calls }
    }
}

actor ControlledCredentialStore: CredentialStoreProtocol {
    let loadResult: CredentialLoadResult
    let saveResult: CredentialSaveResult
    let resetResult: CredentialDeleteResult
    let signOutResult: CredentialDeleteResult
    private var savedCredentials: [Credential] = []
    private var loadCalls = 0
    init(loadResult: CredentialLoadResult, saveResult: CredentialSaveResult = .saved, resetResult: CredentialDeleteResult = .complete, signOutResult: CredentialDeleteResult = .complete) { self.loadResult = loadResult; self.saveResult = saveResult; self.resetResult = resetResult; self.signOutResult = signOutResult }
    func load() -> CredentialLoadResult { loadCalls += 1; return loadResult }
    func save(_ credential: Credential) -> CredentialSaveResult { savedCredentials.append(credential); return saveResult }
    func reset() -> CredentialDeleteResult { resetResult }
    func signOut() -> CredentialDeleteResult { signOutResult }
    func removeDeniedCredential() -> CredentialDeleteResult { resetResult }
    func saved() -> [Credential] { savedCredentials }
    func loadCount() -> Int { loadCalls }
}

final class ControlledRepository: CurrentReleaseRepository, @unchecked Sendable {
    let result: Result<ValidatedRelease, Error>
    init(result: Result<ValidatedRelease, Error>) { self.result = result }
    func fetchCurrentRelease(credential: Credential) async throws -> ValidatedRelease { try result.get() }
}

actor SuspendedRepository: CurrentReleaseRepository {
    private struct Request { let credential: Credential; let continuation: CheckedContinuation<ValidatedRelease, Error> }
    private var requests: [Request] = []
    private var returnedRequestCount = 0
    private var requestWaiters: [CheckedContinuation<Void, Never>] = []
    private var returnWaiters: [CheckedContinuation<Void, Never>] = []
    func fetchCurrentRelease(credential: Credential) async throws -> ValidatedRelease {
        defer { returnedRequestCount += 1; resume(&returnWaiters) }
        return try await withCheckedThrowingContinuation { (continuation: CheckedContinuation<ValidatedRelease, Error>) in
            requests.append(Request(credential: credential, continuation: continuation))
            resume(&requestWaiters)
        }
    }
    func waitForRequests(_ count: Int) async { while requests.count < count { await withCheckedContinuation { requestWaiters.append($0) } } }
    func waitForReturnedRequests(_ count: Int) async { while returnedRequestCount < count { await withCheckedContinuation { returnWaiters.append($0) } } }
    func credential(at index: Int) -> Credential { requests[index].credential }
    func complete(_ index: Int, with result: Result<ValidatedRelease, RepositoryError>) { switch result { case .success(let value): requests[index].continuation.resume(returning: value); case .failure(let error): requests[index].continuation.resume(throwing: error) } }
    func requestCount() -> Int { requests.count }
    private func resume(_ waiters: inout [CheckedContinuation<Void, Never>]) { let current = waiters; waiters.removeAll(); current.forEach { $0.resume() } }
}

@MainActor
extension XCTestCase {
    func waitUntil(
        _ description: String,
        state: SessionState,
        matching condition: @escaping (ScreenState) -> Bool
    ) async throws {
        try Task.checkCancellation()
        guard !condition(state.screen) else { return }

        let changed = expectation(description: description)
        let observation = state.$screen
            .filter(condition)
            .prefix(1)
            .sink { _ in changed.fulfill() }
        defer { observation.cancel() }

        await fulfillment(of: [changed], timeout: 2)
        try Task.checkCancellation()
    }
}
