import Foundation

enum PreviewOriginError: Error, Equatable, Sendable { case missing, invalid }

struct PreviewOrigin: Sendable, Equatable {
    let url: URL

    init(rawValue: String?) throws {
        guard let rawValue, !rawValue.isEmpty else { throw PreviewOriginError.missing }
        let authority = String(rawValue.dropFirst("https://".count))
        let authorityParts = authority.split(separator: ":", omittingEmptySubsequences: false)
        guard authorityParts.count <= 2 else { throw PreviewOriginError.invalid }
        if authorityParts.count == 2 {
            guard let port = Int(authorityParts[1]), (1...65535).contains(port) else { throw PreviewOriginError.invalid }
        }
        guard let candidate = URL(string: rawValue), candidate.scheme == "https", candidate.host != nil,
              candidate.user == nil, candidate.password == nil, candidate.query == nil,
              candidate.fragment == nil, candidate.path == "/" || candidate.path.isEmpty,
              candidate.port.map({ (1...65535).contains($0) }) ?? true else {
            throw PreviewOriginError.invalid
        }
        let allowedHostCharacters = CharacterSet(charactersIn: "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.-")
        guard let host = candidate.host,
              !host.hasPrefix("."),
              !host.contains(".."),
              host.unicodeScalars.allSatisfy({ allowedHostCharacters.contains($0) }) else {
            throw PreviewOriginError.invalid
        }
        self.url = candidate
    }

    func endpointURL() -> URL {
        url.appending(path: "client/api/v1/release/current")
    }
}

struct AppConfiguration: Sendable {
    let origin: Result<PreviewOrigin, PreviewOriginError>
    let expectedAccessGroup: String?

    init(bundle: Bundle = .main) {
        let rawOrigin = ProcessInfo.processInfo.environment["ACE_UI_TEST_NO_ORIGIN"] == "1" ? nil : bundle.object(forInfoDictionaryKey: "ACEPreviewOrigin") as? String
        self.origin = Result { try PreviewOrigin(rawValue: rawOrigin) }
            .mapError { ($0 as? PreviewOriginError) ?? .invalid }
        let accessGroup = bundle.object(forInfoDictionaryKey: "ACEExpectedAccessGroup") as? String
        self.expectedAccessGroup = accessGroup?.isEmpty == false ? accessGroup : nil
    }

    init(origin: Result<PreviewOrigin, PreviewOriginError>, expectedAccessGroup: String? = nil) {
        self.origin = origin
        self.expectedAccessGroup = expectedAccessGroup
    }
}
