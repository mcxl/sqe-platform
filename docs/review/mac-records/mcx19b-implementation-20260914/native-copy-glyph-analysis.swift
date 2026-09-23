import Foundation
import CoreGraphics
import ImageIO
import CryptoKit
var results:[[String:Any]]=[]
for path in CommandLine.arguments.dropFirst() {
 let source=CGImageSourceCreateWithURL(URL(fileURLWithPath:path) as CFURL,nil)!
 let image=CGImageSourceCreateImageAtIndex(source,0,nil)!
 let w=image.width,h=image.height
 var bytes=[UInt8](repeating:0,count:w*h*4)
 bytes.withUnsafeMutableBytes { raw in
  let ctx=CGContext(data:raw.baseAddress,width:w,height:h,bitsPerComponent:8,bytesPerRow:w*4,space:CGColorSpace(name:CGColorSpace.sRGB)!,bitmapInfo:CGImageAlphaInfo.premultipliedLast.rawValue|CGBitmapInfo.byteOrder32Big.rawValue)!
  ctx.draw(image,in:CGRect(x:0,y:0,width:w,height:h))
 }
 func dark(_ x:Int,_ y:Int)->Bool { let i=(y*w+x)*4; return bytes[i]<80 && bytes[i+1]<80 && bytes[i+2]<80 }
 var bands:[[String:Any]]=[]; var y=350
 while y<2600 {
  if !(970..<1200).contains(where:{dark($0,y)}) {y+=1;continue}
  let start=y; var xs:[Int]=[];var rows:[Int]=[]
  while y<2600 && (970..<1200).contains(where:{dark($0,y)}) {
   let row=(970..<1200).filter{dark($0,y)}; xs+=row;rows.append(row.count); y+=1
  }
  let left=xs.min()!,right=xs.max()!;var mask=[UInt8]()
  for yy in start..<y {for xx in left...right {mask.append(dark(xx,yy) ? 1:0)}}
  bands.append(["x":left,"y":start,"width":right-left+1,"height":y-start,"darkPixelCount":xs.count,"rowCounts":rows,"maskSha256":SHA256.hash(data:Data(mask)).map{String(format:"%02x",$0)}.joined()])
 }
 results.append(["file":path,"width":w,"height":h,"darkThreshold":80,"bands":bands])
}
FileHandle.standardOutput.write(try JSONSerialization.data(withJSONObject:results,options:[.prettyPrinted,.sortedKeys]))
