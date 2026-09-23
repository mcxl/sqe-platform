import Foundation
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

    private var showsUITestObservation: Bool {
        UITestScenario.current != nil
            && ProcessInfo.processInfo.environment["ACE_UI_TEST_SHOW_DIAGNOSTICS"] != "0"
    }

    @ViewBuilder
    private var rootContent: some View {
        if showsUITestObservation {
            RootView(state: state)
                .modifier(UITestObservationMetadata())
        } else {
            RootView(state: state)
        }
    }
    #endif

    var body: some Scene {
        WindowGroup {
            Group {
                #if DEBUG
                rootContent
                    .preferredColorScheme(uiTestColorScheme)
                #else
                RootView(state: state)
                #endif
            }
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
private struct UITestObservationMetadata: ViewModifier {
    // Read the window's environment, not the App's scene-level environment.
    @Environment(\.colorScheme) private var colorScheme
    @Environment(\.dynamicTypeSize) private var dynamicTypeSize

    private var contentSizeCategory: String {
        switch dynamicTypeSize {
        case .xSmall: return "extra-small"
        case .small: return "small"
        case .medium: return "medium"
        case .large: return "large"
        case .xLarge: return "extra-large"
        case .xxLarge: return "extra-extra-large"
        case .xxxLarge: return "extra-extra-extra-large"
        case .accessibility1: return "accessibility-medium"
        case .accessibility2: return "accessibility-large"
        case .accessibility3: return "accessibility-extra-large"
        case .accessibility4: return "accessibility-extra-extra-large"
        case .accessibility5: return "accessibility-extra-extra-extra-large"
        @unknown default: return "unknown"
        }
    }


    private var accessibilityValue: String {
        guard ProcessInfo.processInfo.environment["ACE_COVERAGE_OBSERVATIONS"] == "1" else {
            return contentSizeCategory
        }
        let payload: [String: Any] = [
            "appearance": colorScheme == .dark ? "dark" : "light",
            "boldText": UIAccessibility.isBoldTextEnabled,
            "contentSize": contentSizeCategory,
            "increaseContrast": UIAccessibility.isDarkerSystemColorsEnabled,
            "orientation": actualWindowOrientation,
            "reduceMotion": UIAccessibility.isReduceMotionEnabled
        ]
        guard let data = try? JSONSerialization.data(withJSONObject: payload, options: [.sortedKeys]),
              let value = String(data: data, encoding: .utf8) else {
            return contentSizeCategory
        }
        return value
    }

    private var actualWindowOrientation: String {
        let windows = UIApplication.shared.connectedScenes
            .compactMap { $0 as? UIWindowScene }
            .flatMap(\.windows)
        guard let window = windows.first(where: \.isKeyWindow) ?? windows.first else {
            return "unknown"
        }
        return window.bounds.width > window.bounds.height ? "landscape" : "portrait"
    }

    func body(content: Content) -> some View {
        content
            .accessibilityElement(children: .contain)
            .accessibilityIdentifier("Effective interface style")
            .accessibilityLabel(colorScheme == .dark ? "dark" : "light")
            .accessibilityValue(accessibilityValue)
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
