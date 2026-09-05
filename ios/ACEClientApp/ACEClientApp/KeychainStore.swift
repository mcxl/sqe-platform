import Foundation
import Security

protocol SecItemAdapter: AnyObject, Sendable {
    func copyMatching(_ query: [String: Any]) -> (OSStatus, AnyObject?)
    func add(_ attributes: [String: Any]) -> OSStatus
    func update(_ query: [String: Any], attributes: [String: Any]) -> OSStatus
    func delete(_ query: [String: Any]) -> OSStatus
}

final class SystemSecItemAdapter: SecItemAdapter, @unchecked Sendable {
    func copyMatching(_ query: [String: Any]) -> (OSStatus, AnyObject?) {
        var result: CFTypeRef?
        let status = SecItemCopyMatching(query as CFDictionary, &result)
        return (status, result)
    }
    func add(_ attributes: [String: Any]) -> OSStatus { SecItemAdd(attributes as CFDictionary, nil) }
    func update(_ query: [String: Any], attributes: [String: Any]) -> OSStatus { SecItemUpdate(query as CFDictionary, attributes as CFDictionary) }
    func delete(_ query: [String: Any]) -> OSStatus { SecItemDelete(query as CFDictionary) }
}

enum CredentialLoadResult: Sendable, Equatable { case none, credential(Credential), unsafe, failure }
enum CredentialSaveResult: Sendable, Equatable { case saved, saveFailure, deletionPending }
enum CredentialDeleteResult: Sendable, Equatable { case complete, pending }

protocol CredentialStoreProtocol: Sendable {
    func load() async -> CredentialLoadResult
    func save(_ credential: Credential) async -> CredentialSaveResult
    func reset() async -> CredentialDeleteResult
    func signOut() async -> CredentialDeleteResult
    func removeDeniedCredential() async -> CredentialDeleteResult
}

actor CredentialStore: CredentialStoreProtocol {
    nonisolated static let service = "com.auditco.ace.client.authentication"
    nonisolated static let lifecycleOperationsAreSynchronous = true
    nonisolated static let deletionUsesAllSynchronisationClasses = true
    nonisolated static let requiresExactCFTypes = true
    private let adapter: SecItemAdapter
    private let expectedAccessGroup: String?

    init(adapter: SecItemAdapter = SystemSecItemAdapter(), expectedAccessGroup: String? = nil) {
        self.adapter = adapter
        self.expectedAccessGroup = expectedAccessGroup
    }

    // These methods contain no suspension point. The actor cannot re-enter a lifecycle call.
    func load() -> CredentialLoadResult {
        let (status, result) = adapter.copyMatching(inventoryQuery())
        if status == errSecItemNotFound { return .none }
        guard status == errSecSuccess, let list = result as? [[String: Any]], !list.isEmpty else {
            return status == errSecSuccess ? .unsafe : .failure
        }
        guard list.count == 1, let account = validatedAccount(in: list[0], exactAccount: nil) else { return .unsafe }
        let (readStatus, readResult) = adapter.copyMatching(exactReadQuery(account: account))
        if readStatus == errSecItemNotFound { return .unsafe }
        guard readStatus == errSecSuccess else { return .failure }
        guard let item = readResult as? [String: Any],
              validatedAccount(in: item, exactAccount: account) != nil,
              let data = cfData(item[kSecValueData as String]), !data.isEmpty,
              let password = String(data: data, encoding: .utf8), !password.isEmpty else { return .unsafe }
        return .credential(Credential(username: account, password: password))
    }

    func save(_ credential: Credential) -> CredentialSaveResult {
        let (inventoryStatus, result) = adapter.copyMatching(inventoryQuery())
        if inventoryStatus == errSecItemNotFound { return addOrUpdateDuplicate(credential) }
        guard inventoryStatus == errSecSuccess, let list = result as? [[String: Any]], list.count == 1,
              let oldAccount = validatedAccount(in: list[0], exactAccount: nil) else { return .deletionPending }
        if oldAccount == credential.username {
            let status = adapter.update(exactUpdateQuery(account: oldAccount), attributes: [kSecValueData as String: Data(credential.password.utf8)])
            if status == errSecSuccess { return .saved }
            return completedDeletion() ? .saveFailure : .deletionPending
        }
        guard completedDeletion() else { return .deletionPending }
        return addOrUpdateDuplicate(credential)
    }

    func reset() -> CredentialDeleteResult { completedDeletion() ? .complete : .pending }
    func signOut() -> CredentialDeleteResult { completedDeletion() ? .complete : .pending }
    func removeDeniedCredential() -> CredentialDeleteResult { completedDeletion() ? .complete : .pending }

    private func addOrUpdateDuplicate(_ credential: Credential) -> CredentialSaveResult {
        let status = adapter.add(addAttributes(credential))
        if status == errSecSuccess { return .saved }
        guard status == errSecDuplicateItem else { return .saveFailure }
        let update = adapter.update(exactUpdateQuery(account: credential.username), attributes: [kSecValueData as String: Data(credential.password.utf8)])
        if update == errSecSuccess { return .saved }
        return completedDeletion() ? .saveFailure : .deletionPending
    }

    private func completedDeletion() -> Bool {
        let status = adapter.delete(serviceDeletionQuery())
        return status == errSecSuccess || status == errSecItemNotFound
    }

    private func inventoryQuery() -> [String: Any] {
        [kSecClass as String: kSecClassGenericPassword,
         kSecAttrService as String: Self.service,
         kSecAttrSynchronizable as String: kSecAttrSynchronizableAny,
         kSecMatchLimit as String: kSecMatchLimitAll,
         kSecReturnAttributes as String: true,
         kSecReturnData as String: false]
    }

    private func exactReadQuery(account: String) -> [String: Any] {
        [kSecClass as String: kSecClassGenericPassword, kSecAttrService as String: Self.service,
         kSecAttrAccount as String: account, kSecAttrSynchronizable as String: false,
         kSecMatchLimit as String: kSecMatchLimitOne, kSecReturnAttributes as String: true,
         kSecReturnData as String: true]
    }

    private func exactUpdateQuery(account: String) -> [String: Any] {
        [kSecClass as String: kSecClassGenericPassword, kSecAttrService as String: Self.service,
         kSecAttrAccount as String: account, kSecAttrSynchronizable as String: false]
    }

    private func serviceDeletionQuery() -> [String: Any] {
        [kSecClass as String: kSecClassGenericPassword, kSecAttrService as String: Self.service,
         kSecAttrSynchronizable as String: kSecAttrSynchronizableAny]
    }

    private func addAttributes(_ credential: Credential) -> [String: Any] {
        [kSecClass as String: kSecClassGenericPassword, kSecAttrService as String: Self.service,
         kSecAttrAccount as String: credential.username, kSecValueData as String: Data(credential.password.utf8),
         kSecAttrAccessible as String: kSecAttrAccessibleWhenUnlockedThisDeviceOnly,
         kSecAttrSynchronizable as String: false]
    }

    private func validatedAccount(in attributes: [String: Any], exactAccount: String?) -> String? {
        guard let service = cfString(attributes[kSecAttrService as String]), service == Self.service,
              let account = cfString(attributes[kSecAttrAccount as String]), !account.isEmpty,
              exactAccount == nil || account == exactAccount,
              let accessible = cfString(attributes[kSecAttrAccessible as String]),
              accessible == (kSecAttrAccessibleWhenUnlockedThisDeviceOnly as String),
              let synchronizable = cfBoolean(attributes[kSecAttrSynchronizable as String]), !synchronizable else { return nil }
        if let group = attributes[kSecAttrAccessGroup as String] {
            guard let group = cfString(group), let expectedAccessGroup, group == expectedAccessGroup else { return nil }
        }
        for key in [kSecAttrCreationDate as String, kSecAttrModificationDate as String] {
            if let value = attributes[key], !isCFType(value, CFDateGetTypeID()) { return nil }
        }
        return account
    }

    private func cfString(_ value: Any?) -> String? {
        guard let value, isCFType(value, CFStringGetTypeID()) else { return nil }
        return value as? String
    }

    private func cfBoolean(_ value: Any?) -> Bool? {
        guard let value, isCFType(value, CFBooleanGetTypeID()) else { return nil }
        return value as? Bool
    }

    private func cfData(_ value: Any?) -> Data? {
        guard let value, isCFType(value, CFDataGetTypeID()) else { return nil }
        return value as? Data
    }

    private func isCFType(_ value: Any, _ typeID: CFTypeID) -> Bool {
        CFGetTypeID(value as CFTypeRef) == typeID
    }
}
