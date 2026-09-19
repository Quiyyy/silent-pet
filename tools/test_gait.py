from pathlib import Path
import json,math,importlib.util,argparse
from PIL import Image
p=argparse.ArgumentParser(description='Check rendered barefoot gait and wave motion.')
p.add_argument('--root',type=Path,required=True,help='Output directory produced by render_gait.py')
p.add_argument('--renderer',type=Path,default=Path(__file__).with_name('render_gait.py'))
args=p.parse_args();n=args.root.resolve()
spec=importlib.util.spec_from_file_location('motion',args.renderer);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
report=json.loads((n/'qa/walk-trajectory.json').read_text(encoding='utf-8'));fh=report['foot_hull_relative_to_ankle']
for i in range(1001):
 phase=i/1000;dx=.65*math.sin(2*math.pi*phase);dy=.8*math.cos(4*math.pi*phase);a=math.radians(.45*math.sin(2*math.pi*phase));pivot=(108.5,151)
 BM=m.affine(pivot,(118.5,151),(pivot[0]+dx,pivot[1]+dy),(pivot[0]+dx+10*math.cos(a),pivot[1]+dy+10*math.sin(a)))
 feet=[]
 for nominal,offset in [((100,151),.5),((112,151),0)]:
  foot=m.foot_pose(phase+offset,nominal[0],fh);feet.append(foot)
  hip=m.point(BM,nominal);k=m.ik(hip,foot[:2])
  assert abs(math.dist(hip,k)-21.3)<1e-8 and abs(math.dist(k,foot[:2])-22.2)<1e-8
  ang=math.radians(foot[2]);maxy=foot[1]+max(math.sin(ang)*x+math.cos(ang)*y for x,y in fh)
  assert maxy<=201+1e-7
  if foot[3]:assert abs(maxy-201)<1e-7
 assert any(f[3] for f in feet)
assert m.foot_pose(0,112,fh)==m.foot_pose(1,112,fh)
jac=min(leg['min_skin_jacobian'] for f in report['frames'] for leg in f['legs'])
assert jac>0, 'Skin triangle folded or collapsed'
wave=[Image.open(n/'frames/waving'/f'{i:02d}.png').convert('RGBA') for i in range(4)]
assert all(im.crop((84,42,137,97)).tobytes()==wave[0].crop((84,42,137,97)).tobytes() for im in wave)
assert all(im.crop((0,150,192,208)).tobytes()==wave[0].crop((0,150,192,208)).tobytes() for im in wave)
for i in range(8):
 R=Image.open(n/'frames/running-right'/f'{i:02d}.png').convert('RGBA');L=Image.open(n/'frames/running-left'/f'{i:02d}.png').convert('RGBA')
 assert R.transpose(Image.Transpose.FLIP_LEFT_RIGHT).tobytes()==L.tobytes()
out={'ok':True,'trajectory_samples':1001,'no_flight':True,'bone_lengths_preserved':True,'bare_foot_contact_plane_verified':True,'cyclic_path_continuous':True,'rendered_skin_mesh_min_jacobian':jac,'no_folded_rendered_skin_triangles':jac>0,'left_right_phase_mirrored':True,'wave_face_pixels_unchanged':True,'wave_feet_pixels_unchanged':True}
(n/'qa/motion-tests.json').write_text(json.dumps(out,indent=2),encoding='utf-8');print(json.dumps(out))
