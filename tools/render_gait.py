from pathlib import Path
import math,json,argparse
from PIL import Image,ImageDraw,ImageChops,ImageEnhance,ImageFilter
S=3;SIZE=(192*S,208*S)
def components(im,threshold=16):
 a=im.getchannel('A');data=a.tobytes();w,h=im.size;seen=bytearray(w*h);result=[]
 for start,v in enumerate(data):
  if v<=threshold or seen[start]:continue
  todo=[start];seen[start]=1;points=[]
  while todo:
   i=todo.pop();points.append(i);x=i%w;y=i//w
   for j in ([i-1] if x else [])+([i+1] if x<w-1 else [])+([i-w] if y else [])+([i+w] if y<h-1 else []):
    if data[j]>threshold and not seen[j]:seen[j]=1;todo.append(j)
  result.append({'area':len(points),'pixels':points})
 return result
def keep_main(im,require_connected=False):
 cs=sorted(components(im),key=lambda x:x['area'],reverse=True)
 if require_connected and len([c for c in cs if c['area']>32])!=1:raise ValueError('Disconnected anatomical part')
 mask=bytearray(im.width*im.height)
 for i in cs[0]['pixels']:mask[i]=255
 m=Image.frombytes('L',im.size,bytes(mask)).filter(ImageFilter.MaxFilter(5 if im.width>192 else 3))
 out=im.copy();out.putalpha(ImageChops.multiply(im.getchannel('A'),m));return out

def polygon(points):
 m=Image.new('L',SIZE);ImageDraw.Draw(m).polygon([(round(x*S),round(y*S)) for x,y in points],fill=255);return m
def cut(im,mask):
 out=im.copy();out.putalpha(ImageChops.multiply(out.getchannel('A'),mask));return out
def zone(y0,y1):
 return polygon([(0,y0),(192,y0),(192,y1),(0,y1)])
def pivot_layer(im,source_a,source_b,target_a,target_b):
 dx=source_b[0]-source_a[0];dy=source_b[1]-source_a[1]
 ex=target_b[0]-target_a[0];ey=target_b[1]-target_a[1]
 scale=math.hypot(ex,ey)/math.hypot(dx,dy)
 angle=math.atan2(ey,ex)-math.atan2(dy,dx)
 c=math.cos(angle)/scale;s=math.sin(angle)/scale
 ax,ay=[v*S for v in source_a];tx,ty=[v*S for v in target_a]
 coeff=(c,s,ax-c*tx-s*ty,-s,c,ay+s*tx-c*ty)
 return im.transform(SIZE,Image.Transform.AFFINE,coeff,Image.Resampling.BICUBIC)
def ik(hip,ankle,a,b):
 dx=ankle[0]-hip[0];dy=ankle[1]-hip[1];dist=math.hypot(dx,dy)
 if dist>=a+b:raise ValueError('Unreachable ankle')
 along=(a*a-b*b+dist*dist)/(2*dist)
 height=math.sqrt(max(0,a*a-along*along))
 # Bend the knee toward screen-right, never swap branches.
 return (hip[0]+dx/dist*along+dy/dist*height,hip[1]+dy/dist*along-dx/dist*height)
def foot_path(phase,hip_x,stride=12,lift=4):
 q=phase%1;stance=.6
 if q<stance:return (hip_x+stride*(1-2*q/stance),184.0,0.0,True)
 u=(q-stance)/(1-stance);ease=u*u*(3-2*u)
 return (hip_x-stride+2*stride*ease,184-lift*math.sin(math.pi*u),-5*math.sin(math.pi*u),False)
def render(root,source_path):
 root=Path(root)
 for name in ['layers','qa','frames']:(root/name).mkdir(parents=True,exist_ok=True)
 layers=root/'layers'
 src=Image.open(source_path).convert('RGBA')
 master=Image.new('RGBA',SIZE);h=198*S;w=round(src.width*h/src.height)
 master.alpha_composite(src.resize((w,h),Image.Resampling.LANCZOS),((SIZE[0]-w)//2,5*S))

 near_poly=[(93,142),(113,137),(119,146),(125,173),(132,184),(146,189),(149,205),(107,205),(105,181),(98,173),(94,153)]
 all_legs=polygon([(30,151),(170,151),(170,208),(30,208)])
 near_roi=polygon(near_poly)
 green=Image.new('L',SIZE);white=Image.new('L',SIZE)
 px=master.load();gm=green.load();wm=white.load()
 for y in range(SIZE[1]):
  for x in range(SIZE[0]):
   red,g,b,alpha=px[x,y]
   if alpha>32 and g>red*1.07 and g>b*1.2:gm[x,y]=255
   if y<151*S and alpha>32 and min(red,g,b)>140 and max(red,g,b)-min(red,g,b)<65:wm[x,y]=255
 keep=ImageChops.lighter(green.filter(ImageFilter.MaxFilter(7)),white.filter(ImageFilter.MaxFilter(5)))
 # All old legs are cleared; colored cloak and hip-wrap edges remain foreground.
 removal=ImageChops.multiply(all_legs,ImageChops.invert(keep))
 body=master.copy();body.putalpha(ImageChops.multiply(master.getchannel('A'),ImageChops.invert(removal)))
 body=keep_main(body)
 near_mask=ImageChops.multiply(near_roi,ImageChops.invert(ImageChops.lighter(green,white)))
 leg=cut(master,near_mask)
 # Rebuild only a concealed under-wrap attachment with copied trouser texture.
 cap=Image.new('RGBA',SIZE);texture=master.crop((101*S,153*S,112*S,164*S)).resize((18*S,18*S),Image.Resampling.BICUBIC)
 cm=Image.new('L',(18*S,18*S));ImageDraw.Draw(cm).ellipse((0,0,18*S-1,18*S-1),fill=255)
 texture.putalpha(ImageChops.multiply(texture.getchannel('A'),cm));cap.alpha_composite(texture,(94*S,136*S));cap.alpha_composite(leg);leg=cap
 thigh=cut(leg,zone(137,171));shin=cut(leg,zone(158,187));boot=cut(leg,zone(177,208))
 knee_mask=Image.new('L',SIZE);ImageDraw.Draw(knee_mask).ellipse((101*S,155*S,119*S,173*S),fill=255)
 knee_patch=cut(leg,knee_mask)
 for name,im in [('body',body),('thigh',thigh),('shin',shin),('boot',boot),('knee',knee_patch)]:im.save(layers/(name+'.png'))
 source_hip=(103.,145.);source_knee=(110.,164.);source_ankle=(117.,184.)
 lengths=(21.0,21.3)
 times=[120]*7+[220];elapsed=0;frames=[];records=[]
 for index,dt in enumerate(times):
  phase=((elapsed+dt/2)/sum(times)+.025)%1;elapsed+=dt
  canvas=Image.new('RGBA',SIZE);legs=[];bob=.35*math.sin(4*math.pi*phase)
  for name,hip,offset,shade in [('far',(97.,144.+bob),.5,.80),('near',(103.,144.+bob),0,1.)]:
   x,y,angle,stance=foot_path(phase+offset,hip[0]);ankle=(x,y);knee=ik(hip,ankle,*lengths)
   limb=Image.new('RGBA',SIZE)
   limb.alpha_composite(pivot_layer(thigh,source_hip,source_knee,hip,knee))
   limb.alpha_composite(pivot_layer(shin,source_knee,source_ankle,knee,ankle))
   limb.alpha_composite(pivot_layer(knee_patch,source_hip,source_knee,hip,knee))
   end=(ankle[0]+10*math.cos(math.radians(angle)),ankle[1]+10*math.sin(math.radians(angle)))
   limb.alpha_composite(pivot_layer(boot,source_ankle,(source_ankle[0]+10,source_ankle[1]),ankle,end))
   limb=cut(limb,zone(149,208))
   if shade!=1:
    alpha=limb.getchannel('A');limb=ImageEnhance.Brightness(limb).enhance(shade);limb.putalpha(alpha)
   canvas.alpha_composite(limb)
   legs.append({'name':name,'hip':hip,'knee':knee,'ankle':ankle,'foot_angle':angle,'stance':stance})
  canvas.alpha_composite(body.transform(SIZE,Image.Transform.AFFINE,(1,0,0,0,1,-bob*S),Image.Resampling.BICUBIC))
  registered=Image.new('RGBA',SIZE);registered.alpha_composite(canvas,(-4*S,0))
  frame=keep_main(registered.resize((192,208),Image.Resampling.LANCZOS),require_connected=True)
  frames.append(frame);records.append({'frame':index,'duration_ms':dt,'phase':phase,'body_bob_y':bob,'legs':legs})
 out=root/'frames'/'running-right';out.mkdir(parents=True,exist_ok=True)
 left=root/'frames'/'running-left';left.mkdir(parents=True,exist_ok=True)
 for i,f in enumerate(frames):
  f.save(out/f'{i:02d}.png');f.transpose(Image.Transpose.FLIP_LEFT_RIGHT).save(left/f'{i:02d}.png')
 strip=Image.new('RGBA',(1536,208))
 for i,f in enumerate(frames):strip.alpha_composite(f,(i*192,0))
 strip.save(root/'qa/right-rig-strip.png')
 frames[0].save(root/'qa/right-rig.gif',save_all=True,append_images=frames[1:],duration=times,loop=0,disposal=2,optimize=False)
 (root/'qa/rig-trajectory.json').write_text(json.dumps({'frame_durations_ms':times,'body_transform':'shared upright layer; x registration -4px; no rotation/scale changes; vertical bob <=0.35px','registration_x':-4,'source_joints':{'hip':source_hip,'knee':source_knee,'ankle':source_ankle},'leg_lengths':lengths,'frames':records},indent=2),encoding='utf-8')
 layer_sheet=Image.new('RGB',(4*384,450),'#f4f1e5');ld=ImageDraw.Draw(layer_sheet)
 for i,(name,im) in enumerate([('body',body),('thigh',thigh),('shin',shin),('boot',boot)]):
  small=im.resize((384,416));layer_sheet.paste(small,(i*384,25),small);ld.text((i*384+10,5),name,fill='black')
 layer_sheet.save(root/'qa/layers.jpg',quality=86)
 sheet=Image.new('RGB',(1536,2*442),'#f4f1e5');draw=ImageDraw.Draw(sheet)
 for i,f in enumerate(frames):
  x=(i%4)*384;y=(i//4)*442;z=f.resize((384,416),Image.Resampling.NEAREST)
  sheet.paste(z,(x,y+24),z);draw.text((x+8,y+5),f'FRAME {i} {times[i]}ms',fill='black')
 sheet.save(root/'qa/rig-candidate.jpg',quality=88)
 print('Rendered 8 right and 8 mirrored left frames.')
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--output',required=True);parser.add_argument('--source',required=True);args=parser.parse_args();render(args.output,args.source)
