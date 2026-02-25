import AppKit
import Foundation

let n = Int(CommandLine.arguments.count > 1 ? CommandLine.arguments[1] : "1") ?? 1
let performer = NSHapticFeedbackManager.defaultPerformer
for i in 0..<n {
    performer.perform(.generic, performanceTime: .default)
    if i < n - 1 { Thread.sleep(forTimeInterval: 0.3) }
}
