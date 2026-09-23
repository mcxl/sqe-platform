import Foundation
import CoreGraphics
import ImageIO
func luminance(_ rgb: [Int]) -> Double {
    let v=rgb.map { n -> Double in let c=Double(n)/255; return c <= 0.04045 ? c/12.92 : pow((c+0.055)/1.055,2.4) }
    return 0.2126*v[0]+0.7152*v[1]+0.0722*v[2]
}
var output:[[String:Any]]=[]
for name in CommandLine.arguments.dropFirst() {
    let parts=name.components(separatedBy:"|")
    guard parts.count==5 else {fatalError("Expected path|x|y|width|height")}
    let path=parts[0]
    let rect=CGRect(x:Int(parts[1])!,y:Int(parts[2])!,width:Int(parts[3])!,height:Int(parts[4])!)
    guard let source=CGImageSourceCreateWithURL(URL(fileURLWithPath:path) as CFURL,nil),let originalImage=CGImageSourceCreateImageAtIndex(source,0,nil),let image=originalImage.cropping(to:rect),let cs=CGColorSpace(name:CGColorSpace.sRGB) else {fatalError("Cannot read PNG")}
    let width=image.width,height=image.height
    var bytes=[UInt8](repeating:0,count:width*height*4)
    let colours:[Int:Int]=bytes.withUnsafeMutableBytes { raw in
        guard let ctx=CGContext(data:raw.baseAddress,width:width,height:height,bitsPerComponent:8,bytesPerRow:width*4,space:cs,bitmapInfo:CGImageAlphaInfo.premultipliedLast.rawValue|CGBitmapInfo.byteOrder32Big.rawValue) else {fatalError("Cannot decode PNG")}
        ctx.draw(image,in:CGRect(x:0,y:0,width:width,height:height))
        let p=raw.bindMemory(to:UInt8.self)
        var counts:[Int:Int]=[:]
        for i in stride(from:0,to:p.count,by:4) {
            guard p[i+3]==255 else {continue}
            let k=(Int(p[i])<<16)|(Int(p[i+1])<<8)|Int(p[i+2])
            counts[k,default:0]+=1
        }
        return counts
    }
    let sorted=colours.sorted { $0.value > $1.value }
    let frequent=sorted.prefix(6).map { pair -> [String:Any] in
        let rgb=[(pair.key>>16)&255,(pair.key>>8)&255,pair.key&255]
        return ["rgb":rgb,"pixelCount":pair.value,"contrastAgainstBlack":(luminance(rgb)+0.05)/0.05]
    }
    output.append(["file":name,"width":width,"height":height,"sourceColourSpace":image.colorSpace?.name as Any,"analysisColourSpace":"sRGB","blackPixels":colours[0,default:0],"mostFrequentOpaqueColours":frequent])
}
let data=try JSONSerialization.data(withJSONObject:output,options:[.prettyPrinted,.sortedKeys])
FileHandle.standardOutput.write(data)
