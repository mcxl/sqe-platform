import Foundation
import ImageIO
let url=URL(fileURLWithPath:CommandLine.arguments[1])
let s=CGImageSourceCreateWithURL(url as CFURL,nil)!
let p=CGImageSourceCopyPropertiesAtIndex(s,0,nil)! as NSDictionary
print(p)
