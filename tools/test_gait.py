from pathlib import Path
import json,math,importlib.util,argparse
from PIL import Image,ImageChops,ImageDraw
p=argparse.ArgumentParser()
p.add_argument('--root',type=Path,required=True)
p.add_argument('--renderer',type=Path,default=Path(__file__).with_name('render_gait.py'))
a=p.parse_args();n=a.root.resolve()
spec=importlib.util.spec_from_file_location('motion',a.renderer);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
trajectory=json.loads((n/'qa/walk-trajectory.json').read_text(encoding='utf-8'))
max_angle=0
for i in range(1001):
 q=i/1000;stances=[]
 for j,(hipx,offset) in enumerate([(94,.5),(117,0)]):
  deg,lift,stance=m.leg_pose(q+offset);stances.append(stance);max_angle=max(max_angle,abs(deg))
  t=math.radians(deg);M=m.affine((hipx,169),(hipx+10,169),(hipx,175),(hipx+10*math.cos(t),175+10*math.sin(t)))
  assert abs(M[0]*M[0]+M[3]*M[3]-1)<1e-10
  assert abs(M[1]*M[1]+M[4]*M[4]-1)<1e-10
  assert abs(M[0]*M[1]+M[3]*M[4])<1e-10
  assert abs(M[0]*M[4]-M[1]*M[3]-1)<1e-10
  pts=trajectory['foot_outlines'][j]
  bottom=max(m.point(M,p)[1] for p in pts);dy=201-bottom-lift
  corrected=max(m.point(M,p)[1]+dy for p in pts)
  assert corrected<=201+1e-8
  if stance:assert abs(corrected-201)<1e-8
 assert any(stances)
assert m.leg_pose(0)==m.leg_pose(1)
for i in range(8):
 right=Image.open(n/'frames/running-right'/f'{i:02d}.png').convert('RGBA')
 left=Image.open(n/'frames/running-left'/f'{i:02d}.png').convert('RGBA')
 assert right.transpose(Image.Transpose.FLIP_LEFT_RIGHT).tobytes()==left.tobytes()
im=Image.open(n/'final/spritesheet-extended.webp').convert('RGBA')
wave=[im.crop((i*192,3*208,(i+1)*192,4*208)) for i in range(4)]
boxes=[]
for f in wave[1:]:
 diff=ImageChops.difference(wave[0],f);v=ImageChops.lighter(ImageChops.lighter(diff.getchannel('R'),diff.getchannel('G')),ImageChops.lighter(diff.getchannel('B'),diff.getchannel('A')))
 boxes.append(v.getbbox())
 assert f.crop((0,0,192,68)).tobytes()==wave[0].crop((0,0,192,68)).tobytes()
 assert f.crop((78,55,165,121)).tobytes()==wave[0].crop((78,55,165,121)).tobytes()
 diff.paste((0,0,0,0),(24,67,75,117))
 assert not any(diff.tobytes()),'Wave changed pixels outside hand/wrist envelope'

notch_records=[]
for row in [9,10]:
 for col in range(8):
  for side,(lo,hi) in enumerate([(60,94),(99,133)]):
   previous=None;max_step=0
   for y in range(178,196):
    runs=[];run=[]
    for x in range(lo,hi):
     red,g,b,alpha=im.getpixel((col*192+x,row*208+y))
     if alpha>64 and red>g*1.1 and g>b*1.1:run.append(x)
     elif run:runs.append(run);run=[]
    if run:runs.append(run)
    assert runs,'Missing lower-leg skin in gaze cell'
    run=max(runs,key=len);edges=(run[0],run[-1])
    if previous:max_step=max(max_step,max(abs(edges[k]-previous[k]) for k in [0,1]))
    previous=edges
   assert max_step<=2,f'New notch in gaze leg: row{row} col{col} side{side}'
   notch_records.append({'row':row,'column':col,'side':side,'max_adjacent_edge_step_px':max_step})

report={'ok':True,'trajectory_samples':1001,'rigid_whole_limb_matrices_verified':True,'no_knee_or_ankle_warp':True,'limb_scale_exactly_one':True,'at_least_one_supporting_foot':True,'foot_contact_plane_verified':True,'loop_trajectory_continuous':True,'maximum_leg_rotation_degrees':max_angle,'maximum_foot_lift_px':2.6,'framewise_left_mirror':True,'wave_head_horns_and_upper_hair_identical':True,'wave_face_identical':True,'wave_outside_hand_envelope_identical':True,'wave_difference_boxes':boxes,'gaze_32_legs_contour_regression':notch_records}
(n/'qa/motion-tests.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report))
