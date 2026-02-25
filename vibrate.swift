import AppKit
import Foundation

let n = Int(CommandLine.arguments.count > 1 ? CommandLine.arguments[1] : "1") ?? 1

// ── Methode 1 : Acces direct au trackpad (fonctionne en arriere-plan) ──
typealias CreateFunc  = @convention(c) (UInt64) -> UnsafeMutableRawPointer?
typealias OpenFunc    = @convention(c) (UnsafeMutableRawPointer) -> Int32
typealias ActuateFunc = @convention(c) (UnsafeMutableRawPointer, Int32, Int32, Float, Float) -> Int32
typealias CloseFunc   = @convention(c) (UnsafeMutableRawPointer) -> Int32

func vibrateDirectly() -> Bool {
    guard let handle = dlopen(
        "/System/Library/PrivateFrameworks/MultitouchSupport.framework/MultitouchSupport",
        RTLD_NOW
    ) else { return false }

    guard let createSym  = dlsym(handle, "MTActuatorCreateFromDeviceID"),
          let openSym    = dlsym(handle, "MTActuatorOpen"),
          let actuateSym = dlsym(handle, "MTActuatorActuate"),
          let closeSym   = dlsym(handle, "MTActuatorClose") else { return false }

    let create  = unsafeBitCast(createSym,  to: CreateFunc.self)
    let open_   = unsafeBitCast(openSym,    to: OpenFunc.self)
    let actuate = unsafeBitCast(actuateSym, to: ActuateFunc.self)
    let close_  = unsafeBitCast(closeSym,   to: CloseFunc.self)

    // deviceID 0 = trackpad integre, essayer aussi ID connus Apple Silicon
    for deviceID: UInt64 in [0, 1, 2] {
        guard let actuator = create(deviceID) else { continue }
        let rc = open_(actuator)
        if rc != 0 { continue }

        for i in 0..<n {
            // strength 1.0 = vibration maximale
            actuate(actuator, 0, 0, 1.0, 0.0)
            if i < n - 1 { Thread.sleep(forTimeInterval: 0.35) }
        }
        Thread.sleep(forTimeInterval: 0.1)
        close_(actuator)
        return true
    }
    return false
}

// ── Methode 2 : NSHapticFeedbackManager (fallback, prend le focus brievement) ──
func vibrateOfficial() {
    let app = NSApplication.shared
    app.setActivationPolicy(.accessory)

    let window = NSWindow(
        contentRect: NSRect(x: -200, y: -200, width: 1, height: 1),
        styleMask: [], backing: .buffered, defer: false
    )
    window.orderFrontRegardless()
    app.activate(ignoringOtherApps: true)
    RunLoop.current.run(until: Date(timeIntervalSinceNow: 0.05))

    let performer = NSHapticFeedbackManager.defaultPerformer
    for i in 0..<n {
        performer.perform(.levelChange, performanceTime: .now)
        RunLoop.current.run(until: Date(timeIntervalSinceNow: 0.35))
    }
    RunLoop.current.run(until: Date(timeIntervalSinceNow: 0.15))
    window.orderOut(nil)
}

// Essaye la methode directe, sinon fallback
if !vibrateDirectly() {
    vibrateOfficial()
}
