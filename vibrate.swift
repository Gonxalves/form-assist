import AppKit
import Foundation

// 1. NSApplication en mode .accessory (pas .prohibited qui bloque les haptics)
let app = NSApplication.shared
app.setActivationPolicy(.accessory)

// 2. Fenetre invisible hors ecran — requise sur certains macOS pour activer le haptic engine
let window = NSWindow(
    contentRect: NSRect(x: -200, y: -200, width: 1, height: 1),
    styleMask: [],
    backing: .buffered,
    defer: false
)
window.orderFrontRegardless()

let n = Int(CommandLine.arguments.count > 1 ? CommandLine.arguments[1] : "1") ?? 1
let performer = NSHapticFeedbackManager.defaultPerformer

// 3. .levelChange = vibration la plus forte, .now = immediate
for i in 0..<n {
    performer.perform(.levelChange, performanceTime: .now)
    RunLoop.current.run(until: Date(timeIntervalSinceNow: 0.35))
}

RunLoop.current.run(until: Date(timeIntervalSinceNow: 0.15))
