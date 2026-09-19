from pathlib import Path
from PIL import Image,ImageChops,ImageFilter,ImageDraw
import math,json,argparse
COUNTS=[6,8,8,4,5,8,6,6,6]
def skin(p):return p[3]>16 and p[0]>35 and p[0]>p[1]*1.06 and p[1]>p[2]*1.05
def green(p):return p[3]>16 and p[1]>p[0]*1.04 and p[1]>p[2]*1.08
def smooth(x):x=max(0,min(1,x));return x*x*(3-2*x)
def components(mask):
 data=mask.tobytes();w,h=mask.size;seen=bytearray(w*h);out=[]
 for i,v in enumerate(data):
  if not v or seen[i]:continue
  stack=[i];seen[i]=1;pts=[]
  while stack:
   j=stack.pop();pts.append(j);x=j%w;y=j//w
   for k in ([j-1] if x else [])+([j+1] if x<w-1 else [])+([j-w] if y else [])+([j+w] if y<h-1 else []):
    if data[k] and not seen[k]:seen[k]=1;stack.append(k)
  out.append(pts)
 return sorted(out,key=len,reverse=True)
def repair(cell):
 mask=Image.new('L',(192,208));m=mask.load()
 for y in range(174,208):
  for x in range(35,160):
   if skin(cell.getpixel((x,y))):m[x,y]=255
 groups=components(mask.filter(ImageFilter.MaxFilter(3)))[:2]
 assert len(groups)==2
 centers=sorted(sum(i%192 for i in pts)/len(pts) for pts in groups);middle=sum(centers)/2
 out=cell.copy();details=[]
 for side,center in enumerate(centers):
  allowed=(max(20,int(center-22)),min(170,int(center+23)))
  region=Image.new('L',(192,208));rp=region.load()
  for y in range(163,208):
   for x in range(*allowed):
    if (x<middle)==(side==0) and skin(cell.getpixel((x,y))):rp[x,y]=255
  # Keep only the actual connected leg; warm cloak flecks must not enter row bounds.
  pixels=components(region)[0];data=bytearray(192*208)
  for k in pixels:data[k]=255
  region=Image.frombytes('L',(192,208),bytes(data)).filter(ImageFilter.MaxFilter(3));rp=region.load()
  for y in range(208):
   for x in range(192):
    if y<163 or green(cell.getpixel((x,y))):rp[x,y]=0
  part=cell.copy();part.putalpha(ImageChops.multiply(part.getchannel('A'),region))
  bounds={}
  for y in range(163,208):
   xs=[x for x in range(*allowed) if part.getpixel((x,y))[3]>32]
   if xs:bounds[y]=(min(xs),max(xs))
  assert len(bounds)>20
  bottom=max(bounds);top=min(bounds)
  attach=[(a+b)/2 for y,(a,b) in bounds.items() if 164<=y<=168]
  tx=sum(attach)/len(attach)
  foot_center=sum((bounds[y][0]+bounds[y][1])/2 for y in range(bottom-4,bottom+1) if y in bounds)/len([y for y in range(bottom-4,bottom+1) if y in bounds])
  bx=tx+max(-3,min(3,foot_center-tx))
  def shape(y):
   ys=min(bottom,y);neighbors=[bounds[k] for k in range(max(top,ys-2),min(bottom,ys+2)+1)]
   lo=sum(a for a,b in neighbors)/len(neighbors);hi=sum(b for a,b in neighbors)/len(neighbors)
   return lo,hi
  mesh=[]
  for y in range(163,bottom+2):
   lo,hi=shape(y)
   sw=max(1,hi-lo);sc=(lo+hi)/2
   u=(y-166)/max(1,bottom-7-166);target_center=tx+(bx-tx)*smooth(u)
   # Gently tapered cylindrical cartoon shins; the toe contour is retained.
   if y<bottom-8:target_width=15.5-smooth(u)
   else:target_width=sw*min(1,16/max(bounds[k][1]-bounds[k][0] for k in range(bottom-8,bottom+1) if k in bounds))
   weight=smooth((y-163)/9)
   width=sw+(target_width-sw)*weight;cen=sc+(target_center-sc)*weight
   scale=width/sw
   quad=((sc+(0-cen)/scale),y,(sc+(0-cen)/scale),y+1,(sc+(192-cen)/scale),y+1,(sc+(192-cen)/scale),y)
   mesh.append(((0,y*3,576,(y+1)*3),tuple(v*3 for v in quad)))
  replacement=part.resize((576,624),Image.Resampling.LANCZOS).transform((576,624),Image.Transform.MESH,mesh,Image.Resampling.BICUBIC).resize((192,208),Image.Resampling.LANCZOS)
  out.putalpha(ImageChops.multiply(out.getchannel('A'),ImageChops.invert(region)))
  out.alpha_composite(replacement)
  details.append({'side':side,'top_x':tx,'foot_x':bx,'baseline':bottom,'calf_width_px':[15.5,14.5]})
 out.paste(cell.crop((0,0,192,163)),(0,0))
 assert out.crop((0,0,192,163)).tobytes()==cell.crop((0,0,192,163)).tobytes()
 return out,details
def compact(cell):
 out=Image.new('RGBA',(192,208))
 out.paste(cell.crop((0,0,192,163)),(0,8))
 out.paste(cell.crop((0,163,192,201)).resize((192,30),Image.Resampling.LANCZOS),(0,171))
 out.paste(cell.crop((0,201,192,208)),(0,201))
 return out
def process(atlas,output,report):
 im=Image.open(atlas).convert('RGBA');records=[]
 for row in range(11):
  if row in [1,2]:continue
  for col in range(8):
   used=row>=9 or col<COUNTS[row] or (row,col)==(0,6)
   if not used:continue
   cell=im.crop((col*192,row*208,(col+1)*192,(row+1)*208));fixed,legs=repair(cell);fixed=compact(fixed)
   im.paste(fixed,(col*192,row*208));records.append({'row':row,'column':col,'legs':legs})
 im.save(output);Path(report).write_text(json.dumps({'ok':True,'cells':len(records),'method':'straighten painted lower-leg contour, compact toe width; no new anatomy or shoes','protected':'upper body translated down exactly 8px without scaling; lower legs shortened 38px to30px','records':records},indent=2),encoding='utf-8')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--atlas',required=True);p.add_argument('--output',required=True);p.add_argument('--report',required=True);a=p.parse_args();process(a.atlas,a.output,a.report)
