import SwiftUI
import UIKit

@main
struct ACEClientApp: App {
    @UIApplicationDelegateAdaptor(AppDelegate.self) private var appDelegate
    @StateObject private var state = SessionState()

    #if DEBUG
    private var uiTestColorScheme: ColorScheme? {
        guard UITestScenario.current != nil else { return nil }
        switch ProcessInfo.processInfo.environment["ACE_UI_TEST_APPEARANCE"] {
        case "light": return .light
        case "dark": return .dark
        default: return nil
        }
    }
    #endif

    var body: some Scene {
        WindowGroup {
            RootView(state: state)
            #if DEBUG
                .safeAreaInset(edge: .top, spacing: 0) {
                    if UITestScenario.current != nil {
                        EffectiveInterfaceStyleIndicator()
                    }
                }
                .preferredColorScheme(uiTestColorScheme)
            #endif
                .task {
                #if DEBUG
                guard UITestScenario.current == nil else { return }
                #endif
                state.start()
            }
        }
    }
}

#if DEBUG
private struct EffectiveInterfaceStyleIndicator: View {
    // Read the window's environment, not the App's scene-level environment.
    @Environment(\.colorScheme) private var colorScheme

    var body: some View {
        Text(colorScheme == .dark ? "dark" : "light")
            .font(.body)
            .foregroundStyle(.primary)
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(.horizontal)
            .padding(.vertical, 8)
            .background(.background)
            .accessibilityIdentifier("Effective interface style")
    }
}
#endif

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
