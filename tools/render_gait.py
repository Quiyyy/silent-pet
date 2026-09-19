"""Render the approved barefoot gait and optional two-arm wave. Requires Pillow."""
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
def mesh_warp(im,source_map,step=12):
 mesh=[]
 for y in range(0,H,step):
  for x in range(0,W,step):
   r=min(W,x+step);b=min(H,y+step);quad=[]
   for xx,yy in [(x,y),(x,b),(r,b),(r,y)]:
    u,v=source_map(xx,yy);quad.extend((u*S,v*S))
   mesh.append(((x*S,y*S,r*S,b*S),tuple(quad)))
 return im.transform(SIZE,Image.Transform.MESH,mesh,Image.Resampling.BICUBIC)
def hull(points):
 pts=sorted(set(points))
 def cross(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
 lo=[]
 for p in pts:
  while len(lo)>1 and cross(lo[-2],lo[-1],p)<=0:lo.pop()
  lo.append(p)
 hi=[]
 for p in reversed(pts):
  while len(hi)>1 and cross(hi[-2],hi[-1],p)<=0:hi.pop()
  hi.append(p)
 return lo[:-1]+hi[:-1]
def ik(hip,ank,a=21.3,b=22.2):
 dx=ank[0]-hip[0];dy=ank[1]-hip[1];dist=math.hypot(dx,dy)
 if dist>=a+b:raise ValueError('Unreachable ankle')
 k=(a*a-b*b+dist*dist)/(2*dist);h=math.sqrt(max(0,a*a-k*k))
 return (hip[0]+dx/dist*k+dy/dist*h,hip[1]+dy/dist*k-dx/dist*h)
def foot_pose(phase,hip_x,foot_hull,stride=14,lift=5,ground=201):
 q=phase%1;stance=.62
 if q<stance:
  x=hip_x+stride*(1-2*q/stance)
  angle=-6*(1-smooth(q/.12)) if q<.12 else 11*smooth((q-.48)/(.62-.48))
  rise=0
 else:
  u=(q-stance)/(1-stance);x=hip_x-stride+2*stride*smooth(u)
  angle=11-17*smooth(u);rise=lift*math.sin(math.pi*u)
 a=math.radians(angle);extent=max(math.sin(a)*x+math.cos(a)*y for x,y in foot_hull)
 return (x,ground-extent-rise,angle,q<stance,rise)
def skin_mesh(src,transforms):
 # Continuous linear-blend skinning; shared triangle vertices prevent cutout seams.
 dst=Image.new('RGBA',SIZE);alpha=src.getchannel('A');bbox=alpha.getbbox();step=3

 angles=[math.atan2(M[3],M[0]) for M in transforms]
 scales=[math.hypot(M[0],M[3]) for M in transforms]
 knee_target=point(transforms[0],(114,171));ankle_target=point(transforms[1],(119,191.5))
 def mapped(x,y):
  if y<=176:
   w=smooth((y-153)/23);i,j=0,1;origin=(114,171);target=knee_target
  else:
   w=smooth((y-176)/15);i,j=1,2;origin=(119,191.5);target=ankle_target
  delta=(angles[j]-angles[i]+math.pi)%(2*math.pi)-math.pi
  angle=angles[i]+delta*w;scale=scales[i]*(1-w)+scales[j]*w
  dx=x-origin[0];dy=y-origin[1];c=math.cos(angle)*scale;sn=math.sin(angle)*scale
  return (target[0]+c*dx-sn*dy,target[1]+sn*dx+c*dy)
 min_det=1e9
 for y in range(max(0,bbox[1]//S-3),min(H,bbox[3]//S+4),step):
  for x in range(max(0,bbox[0]//S-3),min(W,bbox[2]//S+4),step):
   rr=min(W,x+step);bb=min(H,y+step)
   if not alpha.crop((x*S,y*S,rr*S,bb*S)).getbbox():continue
   vertices=[(x,y),(rr,y),(rr,bb),(x,bb)]
   targets=[mapped(*v) for v in vertices]
   for inds in [(0,1,2),(0,2,3)]:
    sp=[vertices[i] for i in inds];tp=[targets[i] for i in inds]
    dx1,dy1=tp[1][0]-tp[0][0],tp[1][1]-tp[0][1];dx2,dy2=tp[2][0]-tp[0][0],tp[2][1]-tp[0][1]
    det=dx1*dy2-dx2*dy1;min_det=min(min_det,det/(step*step))
    if det<=0:raise ValueError('Folded skin mesh at '+str(sp)+' det='+str(det))
    sx1,sy1=sp[1][0]-sp[0][0],sp[1][1]-sp[0][1];sx2,sy2=sp[2][0]-sp[0][0],sp[2][1]-sp[0][1]
    a=(sx1*dy2-sx2*dy1)/det;b=(-sx1*dx2+sx2*dx1)/det
    d=(sy1*dy2-sy2*dy1)/det;e=(-sy1*dx2+sy2*dx1)/det
    c=sp[0][0]-a*tp[0][0]-b*tp[0][1];f=sp[0][1]-d*tp[0][0]-e*tp[0][1]
    x0=max(0,math.floor(min(v[0] for v in tp)*S));y0=max(0,math.floor(min(v[1] for v in tp)*S))
    x1=min(SIZE[0],math.ceil(max(v[0] for v in tp)*S)+1);y1=min(SIZE[1],math.ceil(max(v[1] for v in tp)*S)+1)
    if x1<=x0 or y1<=y0:continue
    im=src.transform((x1-x0,y1-y0),Image.Transform.AFFINE,(a,b,a*x0+b*y0+c*S,d,e,d*x0+e*y0+f*S),Image.Resampling.BICUBIC)
    mask=Image.new('L',im.size);ImageDraw.Draw(mask).polygon([(round(u*S-x0),round(v*S-y0)) for u,v in tp],fill=255)
    dst.paste(im,(x0,y0),mask)
 return dst,min_det
def prepare_walk(master):
 all_legs=poly([(45,153),(168,153),(168,208),(45,208)])
 near_roi=poly([(107,145),(124,145),(128,183),(146,191),(149,203),(105,206),(104,186),(104,169)])
 green=Image.new('L',SIZE);gm=green.load();px=master.load()
 for y in range(SIZE[1]):
  for x in range(SIZE[0]):
   r,g,b,a=px[x,y]
   if a>32 and g>r*1.07 and g>b*1.2:gm[x,y]=255
 nearby=green.filter(ImageFilter.MaxFilter(17));keep=Image.new('L',SIZE);kp=keep.load();np=nearby.load()
 for y in range(SIZE[1]):
  for x in range(SIZE[0]):
   r,g,b,a=px[x,y]
   if np[x,y] and (gm[x,y] or min(r,g,b)>140 or max(r,g,b)<85):kp[x,y]=255
 body=master.copy();rem=ImageChops.multiply(all_legs,ImageChops.invert(keep));body.putalpha(ImageChops.multiply(master.getchannel('A'),ImageChops.invert(rem)))
 # Clear narrow inner-cape remnants left behind the original legs.
 gap=poly([(90,153),(122,153),(123,178),(89,182)])
 body.putalpha(ImageChops.multiply(body.getchannel('A'),ImageChops.invert(gap)));body=clean_alpha(body)
 leg=cut(master,ImageChops.multiply(near_roi,ImageChops.invert(green)))
 leg=cut(leg,poly([(0,154),(192,154),(192,208),(0,208)]))
 # A concealed skin attachment sits behind the unchanged hip wraps.
 cap=Image.new('RGBA',SIZE);tex=master.crop((112*S,159*S,122*S,169*S)).resize((20*S,20*S),Image.Resampling.BICUBIC)
 m=Image.new('L',tex.size);ImageDraw.Draw(m).ellipse((0,0,20*S-1,20*S-1),fill=255);tex.putalpha(ImageChops.multiply(tex.getchannel('A'),m));cap.alpha_composite(tex,(104*S,140*S));cap.alpha_composite(leg);leg=cap
 foot=cut(leg,poly([(90,187),(160,187),(160,208),(90,208)]))
 pts=[];fa=foot.getchannel('A')
 for y in range(187*S,H*S):
  xs=[x for x in range(90*S,160*S) if fa.getpixel((x,y))>16]
  if xs:pts.extend([(xs[0]/S-119,y/S-191.5),(xs[-1]/S-119,y/S-191.5)])
 return body,leg,foot,hull(pts)
def save_frames(root,state,frames,times):
 folder=root/'frames'/state;folder.mkdir(parents=True,exist_ok=True)
 strip=Image.new('RGBA',(192*len(frames),208))
 for i,f in enumerate(frames):f.save(folder/f'{i:02d}.png');strip.alpha_composite(f,(192*i,0))
 strip.save(root/'qa'/f'{state}-strip.png')
 frames[0].save(root/'qa'/f'{state}.gif',save_all=True,append_images=frames[1:],duration=times,loop=0,disposal=2,optimize=False)
def render_walk(root,source):
 master=normalize(source);body,leg,foot,fh=prepare_walk(master)
 for name,im in [('walk-master',master),('walk-body',body),('bare-leg',leg),('bare-foot',foot)]:im.save(root/'layers'/f'{name}.png')
 hip0=(114,151);knee0=(114,171);ank0=(119,191.5)
 times=[120]*7+[220];elapsed=0;frames=[];records=[]
 for i,dt in enumerate(times):
  phase=((elapsed+dt/2)/sum(times)+.08)%1;elapsed+=dt
  dx=.65*math.sin(2*math.pi*phase);dy=.8*math.cos(4*math.pi*phase);angle=.45*math.sin(2*math.pi*phase)
  a=math.radians(angle);pivot=(108.5,151)
  BM=affine(pivot,(pivot[0]+10,pivot[1]),(pivot[0]+dx,pivot[1]+dy),(pivot[0]+dx+10*math.cos(a),pivot[1]+dy+10*math.sin(a)))
  canvas=Image.new('RGBA',SIZE);details=[]
  for name,nominal,offset,shade in [('far',(100,151),.5,.90),('near',(112,151),0,1)]:
   hip=point(BM,nominal);x,y,fa,stance,rise=foot_pose(phase+offset,nominal[0],fh);ank=(x,y);knee=ik(hip,ank)
   aa=math.radians(fa)
   matrices=[affine(hip0,knee0,hip,knee),affine(knee0,ank0,knee,ank),affine(ank0,(129,191.5),ank,(x+10*math.cos(aa),y+10*math.sin(aa)))]
   limb,jac=skin_mesh(leg,matrices);limb=cut(limb,poly([(0,151),(192,151),(192,208),(0,208)]))
   if shade!=1:
    alpha=limb.getchannel('A');limb=ImageEnhance.Brightness(limb).enhance(shade);limb.putalpha(alpha)
   canvas.alpha_composite(limb)
   details.append({'name':name,'hip':hip,'knee':knee,'ankle':ank,'foot_angle':fa,'stance':stance,'clearance':rise,'min_skin_jacobian':jac})
  def cloth_map(x,y):
   weight=smooth((90-x)/50)*smooth((y-90)/85)
   return (x-.9*math.sin(2*math.pi*phase-.7)*weight,y-.35*math.sin(2*math.pi*phase-1)*weight)
  upper=image_affine(mesh_warp(body,cloth_map),BM);canvas.alpha_composite(upper)
  registered=Image.new('RGBA',SIZE);registered.alpha_composite(canvas,(-6*S,0))
  frame=clean_alpha(registered.resize((192,208),Image.Resampling.LANCZOS),True)
  frames.append(frame);records.append({'frame':i,'duration_ms':dt,'phase':phase,'body_translation':[dx,dy],'body_angle_deg':angle,'legs':details})
 save_frames(root,'running-right',frames,times);save_frames(root,'running-left',[f.transpose(Image.Transpose.FLIP_LEFT_RIGHT) for f in frames],times)
 (root/'qa/walk-trajectory.json').write_text(json.dumps({'foot_hull_relative_to_ankle':fh,'ground_y':201,'bone_lengths':[21.3,22.2],'frames':records},indent=2),encoding='utf-8')
 return frames
def render_wave(root,source):
 master=normalize(source);master.save(root/'layers/wave-master.png');frames=[]
 angles=[-5,3,8,0];records=[]
 for i,deg in enumerate(angles):
  a=math.radians(-deg);c=math.cos(a);s=math.sin(a)
  def arm_map(x,y):
   weight=smooth((x-23)/7)*(1-smooth((x-65)/11))*(1-smooth((y-93)/19))
   dx=x-49;dy=y-91
   xx=49+c*dx-s*dy;yy=91+s*dx+c*dy
   return (x+(xx-x)*weight,y+(yy-y)*weight)
  out=mesh_warp(master,arm_map,step=6);f=clean_alpha(out.resize((192,208),Image.Resampling.LANCZOS),True)
  frames.append(f);records.append({'frame':i,'hand_angle_deg':deg,'wrist_pivot':[49,91],'changed_region':'viewer-left hand/forearm and neighboring flexible hair only; face and holding arm unchanged'})
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
