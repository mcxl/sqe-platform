import Foundation
import AVFoundation
import ImageIO
import UniformTypeIdentifiers
let video = URL(fileURLWithPath: CommandLine.arguments[1])
let output = URL(fileURLWithPath: CommandLine.arguments[2], isDirectory: true)
try FileManager.default.createDirectory(at: output, withIntermediateDirectories: true)
let asset = AVURLAsset(url: video)
let generator = AVAssetImageGenerator(asset: asset)
generator.appliesPreferredTrackTransform = true
generator.requestedTimeToleranceBefore = .zero
generator.requestedTimeToleranceAfter = .zero
let duration = CMTimeGetSeconds(asset.duration)
var results: [[String: Any]] = []
for requested in [47.0,49.0,50.5,51.5,52.5,53.5,55.5,59.0] {
 var actual = CMTime.zero
 let frame = try generator.copyCGImage(at: CMTime(seconds: requested, preferredTimescale: 600), actualTime: &actual)
 let file = output.appendingPathComponent(String(format: "frame-%06.2f.png", requested))
 guard let destination = CGImageDestinationCreateWithURL(file as CFURL, UTType.png.identifier as CFString, 1, nil) else { fatalError("Cannot create PNG") }
 CGImageDestinationAddImage(destination, frame, nil)
 guard CGImageDestinationFinalize(destination) else { fatalError("Cannot write PNG") }
 results.append(["requestedSeconds": requested, "actualSeconds": CMTimeGetSeconds(actual), "width": frame.width, "height": frame.height, "path": file.path])
}
let data = try JSONSerialization.data(withJSONObject: ["durationSeconds": duration, "video": video.path, "frames": results], options: [.prettyPrinted, .sortedKeys])
try data.write(to: output.appendingPathComponent("manifest.json"))
print(String(data: data, encoding: .utf8)!)
