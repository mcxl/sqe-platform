import Foundation

struct Credential: Sendable, Equatable {
    let username: String
    let password: String
}

protocol CurrentReleaseTransport: Sendable {
    func fetchCurrentRelease(request: URLRequest) async throws -> (Data, HTTPURLResponse)
}

protocol CurrentReleaseRepository: Sendable {
    func fetchCurrentRelease(credential: Credential) async throws -> ValidatedRelease
}

enum RepositoryError: Error, Sendable, Equatable {
    case denied, unavailable, noConnection, timeout, secureConnection, invalidResponse
}

enum CurrentReleaseRequest {
    static func make(origin: PreviewOrigin, credential: Credential) throws -> URLRequest {
        var request = URLRequest(url: origin.endpointURL())
        request.httpMethod = "GET"
        request.cachePolicy = .reloadIgnoringLocalCacheData
        request.setValue("application/json", forHTTPHeaderField: "Accept")
        let encoded = Data("\(credential.username):\(credential.password)".utf8).base64EncodedString()
        request.setValue("Basic \(encoded)", forHTTPHeaderField: "Authorization")
        return request
    }
}

struct HTTPCurrentReleaseRepository: CurrentReleaseRepository {
    let origin: PreviewOrigin
    let transport: any CurrentReleaseTransport

    func fetchCurrentRelease(credential: Credential) async throws -> ValidatedRelease {
        do {
            let (data, response) = try await transport.fetchCurrentRelease(request: CurrentReleaseRequest.make(origin: origin, credential: credential))
            switch response.statusCode {
            case 200:
                guard isJSON(response.value(forHTTPHeaderField: "Content-Type")) else { throw RepositoryError.invalidResponse }
                do { return try JSONDecoder().decode(ClientReleaseResponse.self, from: data).validated() }
                catch { throw RepositoryError.invalidResponse }
            case 403: throw RepositoryError.denied
            case 503: throw RepositoryError.unavailable
            default: throw RepositoryError.unavailable
            }
        } catch let error as RepositoryError { throw error }
        catch let error as URLError {
            switch error.code {
            case .timedOut: throw RepositoryError.timeout
            case .serverCertificateUntrusted, .serverCertificateHasBadDate, .serverCertificateHasUnknownRoot, .serverCertificateNotYetValid, .clientCertificateRejected, .secureConnectionFailed, .clientCertificateRequired: throw RepositoryError.secureConnection
            default: throw RepositoryError.noConnection
            }
        } catch { throw RepositoryError.noConnection }
    }

    private func isJSON(_ contentType: String?) -> Bool {
        contentType?.split(separator: ";", maxSplits: 1).first.map { $0.trimmingCharacters(in: .whitespacesAndNewlines).lowercased() == "application/json" } ?? false
    }
}

final class RedirectAndTrustDelegate: NSObject, URLSessionTaskDelegate, @unchecked Sendable {
    func urlSession(_ session: URLSession, task: URLSessionTask, willPerformHTTPRedirection response: HTTPURLResponse, newRequest request: URLRequest, completionHandler: @escaping (URLRequest?) -> Void) {
        completionHandler(nil)
    }

    func urlSession(_ session: URLSession, task: URLSessionTask, didReceive challenge: URLAuthenticationChallenge, completionHandler: @escaping (URLSession.AuthChallengeDisposition, URLCredential?) -> Void) {
        completionHandler(.performDefaultHandling, nil)
    }
}

final class URLSessionCurrentReleaseTransport: CurrentReleaseTransport, @unchecked Sendable {
    let session: URLSession
    private let delegate: RedirectAndTrustDelegate

    init() {
        let configuration = URLSessionConfiguration.ephemeral
        configuration.urlCache = nil
        configuration.requestCachePolicy = .reloadIgnoringLocalCacheData
        configuration.httpCookieStorage = nil
        configuration.httpShouldSetCookies = false
        configuration.urlCredentialStorage = nil
        delegate = RedirectAndTrustDelegate()
        session = URLSession(configuration: configuration, delegate: delegate, delegateQueue: nil)
    }

    func fetchCurrentRelease(request: URLRequest) async throws -> (Data, HTTPURLResponse) {
        let (data, response) = try await session.data(for: request)
        guard let response = response as? HTTPURLResponse else { throw RepositoryError.invalidResponse }
        return (data, response)
    }
}
