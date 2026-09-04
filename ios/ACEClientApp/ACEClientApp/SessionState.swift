import SwiftUI

enum RetryAction: Sendable, Equatable { case refresh, keychainRead, deletion }

enum ScreenState: Equatable, Sendable {
    case configuration
    case signIn(message: String?)
    case loading
    case release(ClientReleaseResponse, notices: [String])
    case empty
    case failure(message: String, retry: RetryAction)
    case deletionPending(message: String, afterDeletion: String?, deletionOnlyRecovery: Bool)

    enum Presentation: Equatable, Sendable {
        case configuration(message: String)
        case signIn(message: String?)
        case loading
        case release(ClientReleaseResponse, notices: [String])
        case empty(message: String)
        case failure(message: String, retry: RetryAction)
        case deletionPending(message: String, deletionOnlyRecovery: Bool)

        var errorMessage: String? {
            switch self {
            case .configuration(let message), .failure(let message, _), .deletionPending(let message, _):
                return message
            case .signIn(let message):
                return message
            case .loading, .release, .empty:
                return nil
            }
        }
    }

    var presentation: Presentation {
        switch self {
        case .configuration:
            return .configuration(message: "This app is not configured for access.")
        case .signIn(let message):
            return .signIn(message: message)
        case .loading:
            return .loading
        case .release(let release, let notices):
            return .release(release, notices: notices)
        case .empty:
            return .empty(message: "No current release is available.")
        case .failure(let message, let retry):
            return .failure(message: message, retry: retry)
        case .deletionPending(let message, _, let deletionOnlyRecovery):
            return .deletionPending(message: message, deletionOnlyRecovery: deletionOnlyRecovery)
        }
    }
}

@MainActor
final class SessionState: ObservableObject {
    @Published private(set) var screen: ScreenState = .loading {
        didSet {
            if screen.presentation.errorMessage != nil { errorAnnouncementEvent &+= 1 }
        }
    }
    @Published private(set) var errorAnnouncementEvent = 0
    private let configuration: AppConfiguration
    private let store: any CredentialStoreProtocol
    private var repository: (any CurrentReleaseRepository)?
    private var credential: Credential?
    private var generation = 0
    private var credentialGeneration = 0
    private var activeTask: Task<Void, Never>?

    init(configuration: AppConfiguration = AppConfiguration(), store: (any CredentialStoreProtocol)? = nil, repository: (any CurrentReleaseRepository)? = nil) {
        self.configuration = configuration
        self.store = store ?? CredentialStore(expectedAccessGroup: configuration.expectedAccessGroup)
        self.repository = repository
    }

    func start() {
        guard case .success(let origin) = configuration.origin else {
            invalidateRequests(); credential = nil; screen = .configuration; return
        }
        if repository == nil { repository = HTTPCurrentReleaseRepository(origin: origin, transport: URLSessionCurrentReleaseTransport()) }
        activeTask?.cancel()
        activeTask = Task { [weak self] in
            guard let self else { return }
            switch await self.store.load() {
            case .none: self.screen = .signIn(message: nil)
            case .credential(let credential): self.credential = credential; self.beginFetch()
            case .unsafe: self.enterDeletionPending(message: "Saved sign-in must be reset before access.", afterDeletion: nil, deletionOnlyRecovery: true)
            case .failure: self.screen = .failure(message: "Saved sign-in could not be read. Try again.", retry: .keychainRead)
            }
        }
    }

    func signIn(username: String, password: String) {
        guard !username.isEmpty, !password.isEmpty else { screen = .signIn(message: "Enter a username and password."); return }
        guard let repository else { screen = .configuration; return }
        invalidateRequests()
        let candidate = Credential(username: username, password: password)
        screen = .loading
        let requestGeneration = generation
        activeTask = Task { [weak self] in
            guard let self else { return }
            do {
                let release = try await repository.fetchCurrentRelease(credential: candidate)
                guard self.canApply(requestGeneration) else { return }
                switch await self.store.save(candidate) {
                case .saved:
                    guard self.canApply(requestGeneration) else { return }
                    self.credential = candidate; self.credentialGeneration += 1; self.apply(release)
                case .saveFailure: self.screen = .signIn(message: "Sign-in could not be saved. Try again.")
                case .deletionPending: self.enterDeletionPending(message: "Saved sign-in could not be removed. Try again.", afterDeletion: nil, deletionOnlyRecovery: false)
                }
            } catch { self.apply(error: error, generation: requestGeneration) }
        }
    }

    func refresh() { beginFetch() }

    func retry(_ action: RetryAction) {
        switch action {
        case .refresh: beginFetch()
        case .keychainRead: start()
        case .deletion: completeDeletion()
        }
    }

    func resetSavedSignIn() { completeDeletion() }

    func signOut() {
        invalidateRequests(); credential = nil; screen = .loading
        activeTask = Task { [weak self] in
            guard let self else { return }
            if await self.store.signOut() == .complete { self.screen = .signIn(message: nil) }
            else { self.enterDeletionPending(message: "Sign-out could not be completed. Try again.", afterDeletion: nil, deletionOnlyRecovery: false) }
        }
    }

    private func beginFetch() {
        guard let credential, let repository else { return }
        invalidateRequests(); screen = .loading
        let requestGeneration = generation
        let requestCredentialGeneration = credentialGeneration
        activeTask = Task { [weak self] in
            guard let self else { return }
            do {
                let release = try await repository.fetchCurrentRelease(credential: credential)
                guard self.canApply(requestGeneration, credentialGeneration: requestCredentialGeneration) else { return }
                self.apply(release)
            } catch { self.apply(error: error, generation: requestGeneration, credentialGeneration: requestCredentialGeneration) }
        }
    }

    private func apply(_ release: ValidatedRelease) {
        switch release {
        case .empty: screen = .empty
        case .release(let release):
            var notices: [String] = []
            if release.conclusion == nil { notices.append("No conclusion is available.") }
            if release.actions.isEmpty { notices.append("No actions are available.") }
            screen = .release(release, notices: notices)
        }
    }

    private func apply(error: Error, generation: Int, credentialGeneration: Int? = nil) {
        guard canApply(generation, credentialGeneration: credentialGeneration) else { return }
        if let error = error as? RepositoryError {
            switch error {
            case .denied:
                invalidateRequests(); credential = nil
                activeTask = Task { [weak self] in
                    guard let self else { return }
                    if await self.store.removeDeniedCredential() == .complete { self.screen = .signIn(message: "Access denied. Sign in again.") }
                    else { self.enterDeletionPending(message: "Saved sign-in could not be removed. Try again.", afterDeletion: "Access denied. Sign in again.", deletionOnlyRecovery: false) }
                }
            case .unavailable, .invalidResponse: applyRequestFailure(message: "ACE is unavailable. Try again later.")
            case .noConnection: applyRequestFailure(message: "ACE could not be reached. Check your connection and try again.")
            case .timeout: applyRequestFailure(message: "The request timed out. Try again.")
            case .secureConnection: applyRequestFailure(message: "ACE could not establish a secure connection. Try again later.")
            }
        } else { applyRequestFailure(message: "ACE could not be reached. Check your connection and try again.") }
    }

    private func applyRequestFailure(message: String) {
        if credential == nil { screen = .signIn(message: message) }
        else { screen = .failure(message: message, retry: .refresh) }
    }

    private func completeDeletion() {
        let afterDeletion: String?
        let deletionOnlyRecovery: Bool
        if case .deletionPending(_, let after, let deletionOnly) = screen {
            afterDeletion = after
            deletionOnlyRecovery = deletionOnly
        } else {
            afterDeletion = nil
            deletionOnlyRecovery = false
        }
        invalidateRequests(); credential = nil; screen = .loading
        activeTask = Task { [weak self] in
            guard let self else { return }
            if await self.store.reset() == .complete { self.screen = .signIn(message: afterDeletion) }
            else { self.enterDeletionPending(message: "Saved sign-in could not be removed. Try again.", afterDeletion: afterDeletion, deletionOnlyRecovery: deletionOnlyRecovery) }
        }
    }

    private func enterDeletionPending(message: String, afterDeletion: String?, deletionOnlyRecovery: Bool) {
        invalidateRequests(); credential = nil; screen = .deletionPending(message: message, afterDeletion: afterDeletion, deletionOnlyRecovery: deletionOnlyRecovery)
    }

    private func invalidateRequests() { generation += 1; activeTask?.cancel(); activeTask = nil }
    private func canApply(_ requestGeneration: Int, credentialGeneration expected: Int? = nil) -> Bool {
        guard !Task.isCancelled, requestGeneration == generation else { return false }
        if let expected { return expected == credentialGeneration && credential != nil }
        if credential != nil { return true }
        if case .loading = screen { return true }
        return false
    }
}
