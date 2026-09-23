import Foundation
import CoreGraphics
import ImageIO
let path = CommandLine.arguments[1]
let source = CGImageSourceCreateWithURL(URL(fileURLWithPath:path) as CFURL,nil)!
let img = CGImageSourceCreateImageAtIndex(source,0,nil)!
let w=img.width,h=img.height
let space=CGColorSpace(name: CGColorSpace.sRGB)!
var data=[UInt8](repeating:0,count:w*h*4)
var histogram=[String:Int]()
data.withUnsafeMutableBytes { b in
 let ctx=CGContext(data:b.baseAddress,width:w,height:h,bitsPerComponent:8,bytesPerRow:w*4,space:space,bitmapInfo:CGImageAlphaInfo.premultipliedLast.rawValue | CGBitmapInfo.byteOrder32Big.rawValue)!
 ctx.draw(img,in:CGRect(x:0,y:0,width:w,height:h))
 for i in stride(from:0,to:w*h*4,by:4) {
  let p=b.bindMemory(to:UInt8.self)
  let key=String(format:"#%02x%02x%02x%02x",p[i],p[i+1],p[i+2],p[i+3])
  histogram[key,default:0]+=1
 }
}
let top=histogram.sorted{$0.value>$1.value}.prefix(10).map{["rgba":$0.key,"pixels":$0.value] as [String:Any]}
let result:[String:Any]=["path":path,"width":w,"height":h,"colorSpace":"sRGB","dominantColors":top]
let out=try JSONSerialization.data(withJSONObject:result,options:[.prettyPrinted,.sortedKeys])
print(String(data:out,encoding:.utf8)!)
