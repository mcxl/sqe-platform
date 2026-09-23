import Foundation
import ImageIO
import UniformTypeIdentifiers
let source=CGImageSourceCreateWithURL(URL(fileURLWithPath:CommandLine.arguments[1]) as CFURL,nil)!
let image=CGImageSourceCreateImageAtIndex(source,0,nil)!
let out=URL(fileURLWithPath:CommandLine.arguments[2])
let dest=CGImageDestinationCreateWithURL(out as CFURL,UTType.png.identifier as CFString,1,nil)!
CGImageDestinationAddImage(dest,image,nil)
assert(CGImageDestinationFinalize(dest))
print("Decoded raw pixel dimensions: \(image.width)x\(image.height)")
