"""Read-only checks for the portable Codex v2 pet package. Requires Pillow."""
from pathlib import Path
import argparse, hashlib, json, sys
from PIL import Image

COUNTS = [6,8,8,4,5,8,6,6,6]
def validate(root):
    errors = []
    manifest = json.loads((root / "pet.json").read_text(encoding="utf-8-sig"))
    if manifest.get("spriteVersionNumber") != 2:
        errors.append("spriteVersionNumber must be2")
    name = manifest.get("spritesheetPath", "")
    if not isinstance(name,str) or not name or Path(name).name != name:
        raise ValueError("spritesheetPath must name a file beside pet.json")
    path = root/name
    with Image.open(path) as opened:
        if opened.format not in ("PNG","WEBP"):
            errors.append("spritesheet must be PNG or WebP")
        im=opened.convert("RGBA")
    if im.size != (1536,2288):
        errors.append(f"Expected1536x2288, found{im.size}")
    else:
        alpha=im.getchannel("A")
        for row in range(11):
            for column in range(8):
                cell=alpha.crop((column*192,row*208,(column+1)*192,(row+1)*208))
                used=row>=9 or column<COUNTS[row] or (row,column)==(0,6)
                if used and sum(v>16 for v in cell.tobytes())<400:
                    errors.append(f"Used cell{row},{column} is empty or too sparse")
                if not used and cell.getbbox() is not None:
                    errors.append(f"Unused cell{row},{column} must be transparent")
        rgba=im.tobytes()
        if any(a==0 and (r or g or b) for r,g,b,a in zip(rgba[0::4],rgba[1::4],rgba[2::4],rgba[3::4])):
            errors.append("Fully transparent pixels contain hidden RGB")
    sha=hashlib.sha256(path.read_bytes()).hexdigest()
    evidence_path=root/"docs/artifact.json"
    if evidence_path.exists():
        evidence=json.loads(evidence_path.read_text(encoding="utf-8-sig"))
        if evidence.get("sha256","").lower()!=sha:
            errors.append("Image hash differs from docs/artifact.json")
    return {"ok":not errors,"spriteVersionNumber":manifest.get("spriteVersionNumber"),"size":list(im.size),"sha256":sha,"errors":errors}

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root",type=Path,default=Path(__file__).resolve().parents[1])
    args=parser.parse_args()
    try:
        result=validate(args.root.resolve())
    except (OSError,ValueError,KeyError) as exc:
        result={"ok":False,"errors":[str(exc)]}
    print(json.dumps(result,indent=2,ensure_ascii=False))
    sys.exit(0 if result["ok"] else 1)
