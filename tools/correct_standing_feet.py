"""One-time repair for the historical shod atlas. Do not apply to the approved barefoot baseline."""
from pathlib import Path
import argparse,math,json,statistics
from PIL import Image,ImageDraw,ImageChops,ImageFilter
COUNTS=[6,8,8,4,5,8,6,6,6]
def med(values):return statistics.median(values)
def skin(p):return p[3]>16 and p[0]>35 and p[0]>p[1]*1.06 and p[1]>p[2]*1.05
def green(p):return p[3]>16 and p[1]>p[0]*1.04 and p[1]>p[2]*1.08
def components(mask):
 data=mask.tobytes();w,h=mask.size;seen=bytearray(w*h);out=[]
 for i,v in enumerate(data):
  if not v or seen[i]:continue
  todo=[i];seen[i]=1;pts=[]
  while todo:
   j=todo.pop();pts.append(j);x=j%w;y=j//w
   for k in ([j-1] if x else [])+([j+1] if x<w-1 else [])+([j-w] if y else [])+([j+w] if y<h-1 else []):
    if data[k] and not seen[k]:seen[k]=1;todo.append(k)
  out.append(pts)
 return sorted(out,key=len,reverse=True)
def feet(im):
 mask=Image.new('L',im.size);m=mask.load()
 for y in range(172,208):
  for x in range(35,160):
   if skin(im.getpixel((x,y))):m[x,y]=255
 mask=mask.filter(ImageFilter.MaxFilter(3));cs=components(mask)[:2]
 if len(cs)!=2 or min(map(len,cs))<100:raise ValueError('Cannot identify two old feet')
 result=[]
 for pts in cs:
  cm=Image.new('L',im.size);data=bytearray(192*208)
  for i in pts:data[i]=255
  cm=Image.frombytes('L',(192,208),bytes(data))
  bbox=cm.getbbox();x0,y0,x1,y1=bbox
  rows=[];colors=[]
  for y in [174,175,176,177,178]:
   xs=[x for x in range(x0,x1) if skin(im.getpixel((x,y))) and cm.getpixel((x,y))]
   if xs:
    rows.append((sum(xs)/len(xs),max(xs)-min(xs)+1))
    for x in xs[len(xs)//4:3*len(xs)//4]:colors.append(im.getpixel((x,y))[:3])
  if len(rows)<2:raise ValueError('Missing calf attachment')
  expanded=cm.filter(ImageFilter.MaxFilter(3))
  candidates=[(x,y) for y in range(180,min(208,y1+2)) for x in range(max(0,x0-1),min(192,x1+1)) if im.getpixel((x,y))[3]>32 and not green(im.getpixel((x,y))) and expanded.getpixel((x,y))]
  baseline=max(y for x,y in candidates)
  bottom=[x for x,y in candidates if y>=baseline-3]
  result.append({'mask':cm,'bbox':bbox,'top_x':med([a for a,b in rows]),'width':med([b for a,b in rows]),'base':baseline,'bottom_x':med(bottom),'color':[med([c[k] for c in colors]) for k in range(3)]})
 return sorted(result,key=lambda x:x['top_x'])
def normalize(path):
 src=Image.open(path).convert('RGBA');S=3;h=198*S;w=round(src.width*h/src.height);out=Image.new('RGBA',(192*S,208*S))
 out.alpha_composite(src.resize((w,h),Image.Resampling.LANCZOS),((192*S-w)//2,5*S));return out
def transform_part(src,scale_x,source_top,source_bottom,target_top,target_bottom,source_base,target_base):
 sy=(target_base-174)/(source_base-174)
 mesh=[]
 for y in range(173,208,2):
  b=min(208,y+2);quad=[]
  for x,yy in [(0,y),(0,b),(192,b),(192,y)]:
   ys=174+(yy-174)/sy;t=max(0,min(1,(ys-176)/15));t=t*t*(3-2*t)
   old_anchor=source_top+(source_bottom-source_top)*t
   new_anchor=target_top+(target_bottom-target_top)*t
   xs=old_anchor+(x-new_anchor)/scale_x;quad.extend((xs*3,ys*3))
  mesh.append(((0,y,192,b),tuple(quad)))
 return src.transform((192,208),Image.Transform.MESH,mesh,Image.Resampling.BICUBIC)
def process(atlas_path,reference,output,report_path):
 atlas=Image.open(atlas_path).convert('RGBA');original=atlas.copy();high=normalize(reference);low=high.resize((192,208),Image.Resampling.LANCZOS);refs=feet(low)
 sources=[]
 for f in refs:
  x0,_,x1,_=f['bbox'];mask=Image.new('L',high.size);ImageDraw.Draw(mask).rectangle(((x0-2)*3,173*3,(x1+2)*3,208*3),fill=255)
  im=high.copy();im.putalpha(ImageChops.multiply(high.getchannel('A'),mask));sources.append(im)
 targets=[]
 for row in range(11):
  for col in range(8):
   if row in [1,2,3]:continue
   used=row>=9 or col<COUNTS[row] or (row,col)==(0,6)
   if not used:continue
   cell=atlas.crop((col*192,row*208,(col+1)*192,(row+1)*208))
   fs=feet(cell);group='look' if row>=9 or (row,col)==(0,6) else str(row)
   targets.append({'row':row,'col':col,'cell':cell,'feet':fs,'group':group})
 groups={}
 for t in targets:groups.setdefault(t['group'],[]).append(t)
 stats={}
 for name,group in groups.items():
  stats[name]=[]
  for side in [0,1]:
   fs=[g['feet'][side] for g in group]
   stats[name].append({'scale':min(1.5,max(.8,med([f['width'] for f in fs])/refs[side]['width'])),'color':[med([f['color'][k] for f in fs]) for k in range(3)],'ground':med([f['base'] for f in fs]),'bottom_x':med([f['bottom_x'] for f in fs])})
 records=[]
 for t in targets:
  old=t['cell'];patched=old.copy();legs=[]
  for side,f in enumerate(t['feet']):
   st=stats[t['group']][side];base=round(st['ground']) if t['group']=='look' else f['base'];bottom=st['bottom_x'] if t['group']=='look' else f['bottom_x']
   gain=[min(1.15,max(.85,st['color'][k]/refs[side]['color'][k])) for k in range(3)]
   src=sources[side].copy();channels=src.split();src=Image.merge('RGBA',tuple(channels[k].point([min(255,round(v*gain[k])) for v in range(256)]) for k in range(3))+(channels[3],))
   replacement=transform_part(src,st['scale'],refs[side]['top_x'],refs[side]['bottom_x'],f['top_x'],bottom,refs[side]['base'],base)
   remove=f['mask'].filter(ImageFilter.MaxFilter(5));rm=remove.load();px=old.load()
   for y in range(208):
    for x in range(192):
     if y<173 or green(px[x,y]):rm[x,y]=0
   patched.putalpha(ImageChops.multiply(patched.getchannel('A'),ImageChops.invert(remove)))
   patched.alpha_composite(replacement)
   legs.append({'side':side,'top_x':f['top_x'],'bottom_x':bottom,'baseline':base,'width_scale':st['scale'],'color_gain':gain})
  blend=Image.new('L',(192,208));d=ImageDraw.Draw(blend)
  for y in range(174,208):
   v=min(1,max(0,(y-174)/5));v=v*v*(3-2*v);d.line((0,y,192,y),fill=round(255*v))
  result=Image.composite(patched,old,blend)
  assert result.crop((0,0,192,174)).tobytes()==old.crop((0,0,192,174)).tobytes()
  atlas.paste(result,(t['col']*192,t['row']*208))
  records.append({'row':t['row'],'column':t['col'],'feet':legs})
 atlas.save(output)
 Path(report_path).write_text(json.dumps({'ok':True,'cells_corrected':len(targets),'feet_corrected':2*len(targets),'protected_pixels':'Rows above y174 in each corrected cell unchanged before final edge cleanup','gaze_feet':'Shared positions, width and color for all 16 directions and neutral; calf attachment retained per cell','records':records},indent=2),encoding='utf-8')
 print(json.dumps({'ok':True,'cells_corrected':len(targets),'feet_corrected':2*len(targets)}))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--atlas',required=True);p.add_argument('--reference',required=True);p.add_argument('--output',required=True);p.add_argument('--report',required=True);a=p.parse_args();process(a.atlas,a.reference,a.output,a.report)
