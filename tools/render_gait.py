"""Render short cartoon legs as rigid limbs and wave an isolated hand. Requires Pillow."""
from pathlib import Path
import math,json,argparse
from PIL import Image,ImageDraw,ImageChops,ImageEnhance,ImageFilter
S=3;W=192;H=208;SIZE=(W*S,H*S)
def smooth(t):
 t=max(0,min(1,t));return t*t*(3-2*t)
def components(im):
 data=im.getchannel('A').tobytes();w,h=im.size;seen=bytearray(w*h);out=[]
 for i,v in enumerate(data):
  if v<=16 or seen[i]:continue
  stack=[i];seen[i]=1;pts=[]
  while stack:
   j=stack.pop();pts.append(j);x=j%w;y=j//w
   for k in ([j-1] if x else [])+([j+1] if x<w-1 else [])+([j-w] if y else [])+([j+w] if y<h-1 else []):
    if data[k]>16 and not seen[k]:seen[k]=1;stack.append(k)
  out.append(pts)
 return sorted(out,key=len,reverse=True)
def clean_alpha(im,strict=False):
 cs=components(im)
 if strict and len([x for x in cs if len(x)>32])!=1:raise ValueError('Detached anatomical part')
 mask=bytearray(im.width*im.height)
 for i in cs[0]:mask[i]=255
 m=Image.frombytes('L',im.size,bytes(mask)).filter(ImageFilter.MaxFilter(5 if im.width>192 else 3))
 out=im.copy();out.putalpha(ImageChops.multiply(out.getchannel('A'),m));return out
def poly(points):
 m=Image.new('L',SIZE);ImageDraw.Draw(m).polygon([(round(x*S),round(y*S)) for x,y in points],fill=255);return m
def cut(im,m):
 out=im.copy();out.putalpha(ImageChops.multiply(out.getchannel('A'),m));return out
def normalize(path):
 im=Image.open(path).convert('RGBA');h=198*S;w=round(im.width*h/im.height);out=Image.new('RGBA',SIZE)
 out.alpha_composite(im.resize((w,h),Image.Resampling.LANCZOS),((SIZE[0]-w)//2,5*S));return out
def affine(a,b,c,d):
 x,y=b[0]-a[0],b[1]-a[1];u,v=d[0]-c[0],d[1]-c[1];den=x*x+y*y
 A=(u*x+v*y)/den;B=(v*x-u*y)/den
 return (A,-B,c[0]-A*a[0]+B*a[1],B,A,c[1]-B*a[0]-A*a[1])
def point(M,p):return (M[0]*p[0]+M[1]*p[1]+M[2],M[3]*p[0]+M[4]*p[1]+M[5])
def inverse(M):
 a,b,c,d,e,f=M;det=a*e-b*d
 return (e/det,-b/det,(b*f-e*c)/det,-d/det,a/det,(d*c-a*f)/det)
def image_affine(im,M):
 a,b,c,d,e,f=inverse(M)
 return im.transform(SIZE,Image.Transform.AFFINE,(a,b,c*S,d,e,f*S),Image.Resampling.BICUBIC)
def prepare_walk(master):
 # Short legs are painted as complete cartoon limbs; retain their original contours.
 green=Image.new('L',SIZE);px=master.load();gp=green.load()
 for y in range(160*S,H*S):
  for x in range(W*S):
   r,g,b,a=px[x,y]
   if a>16 and g>r*1.04 and g>b*1.08:gp[x,y]=255
 cape=green.filter(ImageFilter.MaxFilter(5))
 rois=[poly([(83,170),(105,174),(105,197),(79,197),(79,183)]),
       poly([(109,172),(130,172),(132,198),(105,198),(105,184)])]
 legs=[cut(master,ImageChops.multiply(m,ImageChops.invert(cape))) for m in rois]
 remove=ImageChops.lighter(rois[0],rois[1]);remove=ImageChops.multiply(remove,ImageChops.invert(cape))
 body=master.copy();body.putalpha(ImageChops.multiply(master.getchannel('A'),ImageChops.invert(remove)))
 # Cape tips are shortened to meet the feet, while face/scroll stay exactly shaped.
 fixed=Image.new('RGBA',SIZE);fixed.alpha_composite(body.crop((0,0,W*S,177*S)),(0,0))
 hem=body.crop((0,177*S,W*S,H*S)).resize((W*S,19*S),Image.Resampling.LANCZOS)
 fixed.alpha_composite(hem,(0,177*S));body=clean_alpha(fixed)
 return body,legs

def save_frames(root,state,frames,times):
 folder=root/'frames'/state;folder.mkdir(parents=True,exist_ok=True)
 strip=Image.new('RGBA',(192*len(frames),208))
 for i,f in enumerate(frames):f.save(folder/f'{i:02d}.png');strip.alpha_composite(f,(192*i,0))
 strip.save(root/'qa'/f'{state}-strip.png')
 frames[0].save(root/'qa'/f'{state}.gif',save_all=True,append_images=frames[1:],duration=times,loop=0,disposal=2,optimize=False)
def leg_pose(phase):
 q=phase%1;stance=.56
 if q<stance:shift=4.5*(1-2*q/stance);rise=0
 else:
  u=(q-stance)/(1-stance);shift=-4.5+9*smooth(u);rise=2.6*math.sin(math.pi*u)
 return math.degrees(math.asin(-shift/30)),rise,q<stance

def render_walk(root,source):
 master=normalize(source);body,legs=prepare_walk(master)
 for name,im in [('walk-master',master),('walk-body',body),('short-far-leg',legs[0]),('short-near-leg',legs[1])]:im.save(root/'layers'/f'{name}.png')
 times=[120]*7+[220];elapsed=0;frames=[];records=[]
 outlines=[]
 for leg in legs:
  pts=[];aa=leg.getchannel('A')
  for y in range(186*S,201*S):
   xs=[x for x in range(70*S,139*S) if aa.getpixel((x,y))>32]
   if xs:pts.extend([(xs[0]/S,y/S),(xs[-1]/S,y/S)])
  outlines.append(pts)
 for i,dt in enumerate(times):
  phase=((elapsed+dt/2)/sum(times)+.03)%1;elapsed+=dt
  canvas=Image.new('RGBA',SIZE);details=[]
  for j,(name,hipx,offset) in enumerate([('far',94,.5),('near',117,0)]):
   angle,rise,stance=leg_pose(phase+offset);a=math.radians(angle)
   M=affine((hipx,169),(hipx+10,169),(hipx,175),(hipx+10*math.cos(a),175+10*math.sin(a)))
   bottom=max(point(M,p)[1] for p in outlines[j])
   M=(M[0],M[1],M[2],M[3],M[4],M[5]+201-bottom-rise)
   canvas.alpha_composite(image_affine(legs[j],M))
   details.append({'name':name,'angle_deg':angle,'lift_px':rise,'stance':stance,'matrix':M,'shape_scale':1})
  body_shift=.3*math.cos(4*math.pi*phase)
  canvas.alpha_composite(image_affine(body,(1,0,0,0,1,6+body_shift)))
  f=clean_alpha(canvas.resize((W,H),Image.Resampling.LANCZOS),True)
  frames.append(f);records.append({'frame':i,'duration_ms':dt,'phase':phase,'body_y':6+body_shift,'legs':details})
 save_frames(root,'running-right',frames,times);save_frames(root,'running-left',[f.transpose(Image.Transpose.FLIP_LEFT_RIGHT) for f in frames],times)
 (root/'qa/walk-trajectory.json').write_text(json.dumps({'method':'painted short cartoon legs rotated as complete rigid limbs; no knee/ankle deformation','ground_y':201,'foot_outlines':outlines,'frames':records},indent=2),encoding='utf-8')
 return frames

def wave_layers(master):
 roi=poly([(24,62),(64,62),(65,89),(57,97),(40,98),(34,91),(24,86)])
 skin=Image.new('L',SIZE);sp=skin.load();px=master.load();rp=roi.load()
 for y in range(62*S,98*S):
  for x in range(24*S,66*S):
   red,g,b,a=px[x,y]
   if rp[x,y] and a>16 and red>g*1.07 and g>b*1.08:sp[x,y]=255
 skin_rgba=Image.new('RGBA',SIZE);skin_rgba.putalpha(skin)
 keep=bytearray(SIZE[0]*SIZE[1])
 for k in components(skin_rgba)[0]:keep[k]=255
 skin=Image.frombytes('L',SIZE,bytes(keep))
 mask=skin.filter(ImageFilter.MaxFilter(5))
 hand=cut(master,mask)
 # A fixed hair backplate is revealed behind the waving hand; it never deforms.
 clean=master.copy();clean.putalpha(ImageChops.multiply(clean.getchannel('A'),ImageChops.invert(mask)))
 hair=master.crop((52*S,51*S,65*S,65*S)).resize((24*S,37*S),Image.Resampling.BICUBIC)
 backing=Image.new('RGBA',SIZE);backing.alpha_composite(hair,(40*S,62*S))
 hair_shape=poly([(48,62),(64,62),(64,97),(39,97),(39,89),(44,80)])
 backing=cut(backing,ImageChops.multiply(mask,hair_shape));clean.alpha_composite(backing)
 return clean,hand,mask

def render_wave(root,source):
 from shape_cartoon_legs import compact,repair
 master=normalize(source);master.save(root/'layers/wave-master.png');frames=[];records=[]
 base,hand,mask=wave_layers(master)
 for name,im in [('wave-static-body',base),('wave-hand',hand),('wave-hand-mask',mask)]:im.save(root/'layers'/f'{name}.png')
 # The wrist is the only pivot. Head, horns, hair and torso do not enter the transform.
 for i,angle in enumerate([-3,2,5,0]):
  a=math.radians(angle);M=affine((47,93),(57,93),(47,93),(47+10*math.cos(a),93+10*math.sin(a)))
  frame=base.copy();frame.alpha_composite(image_affine(hand,M))
  f=clean_alpha(frame.resize((W,H),Image.Resampling.LANCZOS),True)
  f=compact(repair(f)[0])
  frames.append(f);records.append({'frame':i,'hand_angle_deg':angle,'wrist_pivot':[47,93],'transformed_parts':'isolated hand only; forearm and all hair/head/body static'})
 save_frames(root,'waving',frames,[140,140,140,280])
 (root/'qa/wave-motion.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
 return frames

def main():
 p=argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--walk-source','--source',dest='walk_source',required=True);p.add_argument('--wave-source');a=p.parse_args();root=Path(a.output)
 for folder in ['layers','frames','qa']:(root/folder).mkdir(parents=True,exist_ok=True)
 walk=render_walk(root,a.walk_source);wave=render_wave(root,a.wave_source) if a.wave_source else []
 for name,fs in [('walk',walk),('wave',wave)]:
  sheet=Image.new('RGB',(1536,2*442),'#f4f1e5');d=ImageDraw.Draw(sheet)
  for i,f in enumerate(fs):
   x=(i%4)*384;y=(i//4)*442;z=f.resize((384,416),Image.Resampling.NEAREST);sheet.paste(z,(x,y+24),z);d.text((x+8,y+4),name+' '+str(i),fill='black')
  sheet.save(root/'qa'/f'{name}-candidate.jpg',quality=87)
 print(f'Rendered 8 right, 8 left and {len(wave)} waving frames.')
if __name__=='__main__':main()
