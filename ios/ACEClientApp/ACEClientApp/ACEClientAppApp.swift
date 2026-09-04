import SwiftUI
import UIKit

@main
struct ACEClientApp: App {
    @UIApplicationDelegateAdaptor(AppDelegate.self) private var appDelegate
    @StateObject private var state = SessionState()

    var body: some Scene {
        WindowGroup {
            RootView(state: state).task {
                #if DEBUG
                guard UITestScenario.current == nil else { return }
                #endif
                state.start()
            }
        }
    }
}

@MainActor
final class AppDelegate: NSObject, UIApplicationDelegate {
    func application(_ application: UIApplication, configurationForConnecting connectingSceneSession: UISceneSession, options: UIScene.ConnectionOptions) -> UISceneConfiguration {
        let configuration = UISceneConfiguration(name: nil, sessionRole: connectingSceneSession.role)
        configuration.delegateClass = PrivacySceneDelegate.self
        return configuration
    }
}

@MainActor
final class PrivacySceneDelegate: NSObject, UIWindowSceneDelegate {
    private var cover: UIWindow?

    func sceneWillResignActive(_ scene: UIScene) {
        guard let windowScene = scene as? UIWindowScene else { return }
        let cover = UIWindow(windowScene: windowScene)
        cover.windowLevel = .alert + 1
        cover.rootViewController = UIHostingController(rootView: PrivacyCoverView())
        UIView.performWithoutAnimation { cover.isHidden = false }
        self.cover = cover
    }

    func sceneDidBecomeActive(_ scene: UIScene) {
        guard let cover else { return }
        UIView.performWithoutAnimation { cover.isHidden = true }
        self.cover = nil
    }
}
