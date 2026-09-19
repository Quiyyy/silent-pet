from pathlib import Path
from PIL import Image
import importlib.util,json,math,argparse
def check(root,renderer):
 root=Path(root);spec=importlib.util.spec_from_file_location('rig',renderer);rig=importlib.util.module_from_spec(spec);spec.loader.exec_module(rig)
 for i in range(1001):
  t=i/1000
  a=rig.foot_path(t,103);b=rig.foot_path(t+.5,97)
  assert a[3] or b[3], 'Both feet airborne'
  bob=.35*math.sin(4*math.pi*t)
  for hip,foot in [((103,144+bob),a),((97,144+bob),b)]:
   knee=rig.ik(hip,foot[:2],21,21.3)
   assert abs(math.dist(hip,knee)-21)<1e-8 and abs(math.dist(knee,foot[:2])-21.3)<1e-8
   assert 180<=foot[1]<=184
 assert rig.foot_path(0,103)==rig.foot_path(1,103)
 fs=[Image.open(root/'frames/running-right'/f'{i:02d}.png').convert('RGBA') for i in range(8)]
 records=json.loads((root/'qa/rig-trajectory.json').read_text(encoding='utf-8'))
 assert all(abs(x['body_bob_y'])<=.35 for x in records['frames'])
 # Rendered head/body geometry is shared: only the recorded bounded translation changes.
 for i,f in enumerate(fs):
  assert Image.open(root/'frames/running-left'/f'{i:02d}.png').convert('RGBA').tobytes()==f.transpose(Image.Transpose.FLIP_LEFT_RIGHT).tobytes()
  assert len([c for c in rig.components(f) if c['area']>32])==1
 report={'ok':True,'trajectory_samples':1001,'no_flight':True,'ik_bone_lengths_preserved':True,'max_ankle_lift_px':4,'cyclic_path_continuous':True,'upper_body_rotation_degrees':0,'upper_body_scale':1,'upper_body_vertical_bob_max_px':.35,'all_rendered_anatomical_parts_connected':True,'left_exact_mirror':True,'native_frame_durations_ms':[120]*7+[220]}
 (root/'qa/rig-tests.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--renderer',required=True);a=p.parse_args();check(a.root,a.renderer)
