import Foundation
import AVFoundation
import ImageIO
import UniformTypeIdentifiers
let source = CommandLine.arguments[1]
let destination = URL(fileURLWithPath: CommandLine.arguments[2], isDirectory: true)
try FileManager.default.createDirectory(at: destination, withIntermediateDirectories: true)
let asset = AVURLAsset(url: URL(fileURLWithPath: source))
let generator = AVAssetImageGenerator(asset: asset)
generator.appliesPreferredTrackTransform = true
generator.requestedTimeToleranceBefore = .zero
generator.requestedTimeToleranceAfter = .zero
var rows: [[String: Any]] = []
for value in CommandLine.arguments.dropFirst(3) {
    guard let seconds = Double(value) else { fatalError("Invalid time") }
    var actual = CMTime.zero
    let frame = try generator.copyCGImage(at: CMTime(seconds: seconds, preferredTimescale: 600), actualTime: &actual)
    let name = "frame-" + value + ".png"
    let url = destination.appendingPathComponent(name)
    guard let writer = CGImageDestinationCreateWithURL(url as CFURL, UTType.png.identifier as CFString, 1, nil) else { fatalError("No PNG writer") }
    CGImageDestinationAddImage(writer, frame, nil)
    guard CGImageDestinationFinalize(writer) else { fatalError("PNG write failed") }
    rows.append(["requestedSeconds": seconds, "actualSeconds": actual.seconds, "file": name, "width": frame.width, "height": frame.height])
}
let record: [String: Any] = ["source": source, "durationSeconds": asset.duration.seconds, "frames": rows, "limitation": "Retained screen-recording frames do not identify the private accessibility audit sample times."]
let data = try JSONSerialization.data(withJSONObject: record, options: [.prettyPrinted, .sortedKeys])
try data.write(to: destination.appendingPathComponent("frames.json"))
print(String(data: data, encoding: .utf8)!)
