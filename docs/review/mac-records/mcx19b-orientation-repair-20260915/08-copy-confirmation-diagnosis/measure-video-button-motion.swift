import Foundation
import AVFoundation
import CoreVideo
let asset=AVURLAsset(url:URL(fileURLWithPath:CommandLine.arguments[1]))
let reader=try AVAssetReader(asset:asset)
let track=asset.tracks(withMediaType:.video).first!
let output=AVAssetReaderTrackOutput(track:track,outputSettings:[kCVPixelBufferPixelFormatTypeKey as String:kCVPixelFormatType_32BGRA])
output.alwaysCopiesSampleData=false
reader.add(output)
reader.timeRange=CMTimeRange(start:CMTime(seconds:200,preferredTimescale:600),duration:CMTime(seconds:17,preferredTimescale:600))
reader.startReading()
var rows:[[String:Any]]=[]
while let sample=output.copyNextSampleBuffer() {
 let stamp=CMTimeGetSeconds(CMSampleBufferGetPresentationTimeStamp(sample))
 guard let buffer=CMSampleBufferGetImageBuffer(sample) else {continue}
 CVPixelBufferLockBaseAddress(buffer,.readOnly)
 let w=CVPixelBufferGetWidth(buffer),h=CVPixelBufferGetHeight(buffer),stride=CVPixelBufferGetBytesPerRow(buffer)
 let raw=CVPixelBufferGetBaseAddress(buffer)!.assumingMemoryBound(to:UInt8.self)
 var ys:[Int]=[]
 if w==1206 && h==2622 {
  for y in 1000..<min(h,2500) {
   var count=0
   for x in 96..<528 {
    let i=y*stride+x*4
    if abs(Int(raw[i])-203)<=8 && abs(Int(raw[i+1])-198)<=8 && abs(Int(raw[i+2])-198)<=8 {count+=1}
   }
   if count>100 {ys.append(y)}
  }
 }
 CVPixelBufferUnlockBaseAddress(buffer,.readOnly)
 rows.append(["videoSeconds":stamp,"greyButtonTopPixels":ys.first as Any? ?? NSNull(),"greyButtonBottomPixels":ys.last as Any? ?? NSNull()])
}
let data=try JSONSerialization.data(withJSONObject:["status":reader.status.rawValue,"error":reader.error?.localizedDescription as Any? ?? NSNull(),"method":"Pixel rows in x96..<528,y1000..<2500 with more than100 pixels within8 RGB levels of button grey. Video pixels are compressed.","samples":rows],options:[.prettyPrinted,.sortedKeys])
print(String(data:data,encoding:.utf8)!)
