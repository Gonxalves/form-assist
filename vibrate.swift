import AppKit
import Foundation

// NSApplication + RunLoop requis pour que le trackpad vibre reellement
let app = NSApplication.shared
app.setActivationPolicy(.prohibited)   // pas d'icone Dock

let n = Int(CommandLine.arguments.count > 1 ? CommandLine.arguments[1] : "1") ?? 1
let performer = NSHapticFeedbackManager.defaultPerformer

for i in 0..<n {
    performer.perform(.generic, performanceTime: .default)
    // RunLoop traite les evenements hardware (Thread.sleep ne le fait pas)
    RunLoop.current.run(until: Date(timeIntervalSinceNow: 0.3))
}

// Laisser le temps au dernier haptic de se declencher
RunLoop.current.run(until: Date(timeIntervalSinceNow: 0.1))
