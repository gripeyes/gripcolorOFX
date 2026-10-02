"""Evaluate a versioned operator specification on float32 RGBA samples or .npy images."""
import argparse,json,sys
from pathlib import Path
import numpy as np
import _rendition as c
EFFECTS=['Scene','Tone','Volume','Density','Crossover','Crosstalk','Strip','Inspector']
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('spec',type=Path,help='JSON schema_version=1, effect, parameters, metadata, and optional samples')
    parser.add_argument('--input',type=Path,help='Float image .npy with shape (...,4)')
    parser.add_argument('--output',type=Path,help='Write output .npy (otherwise JSON samples)')
    args=parser.parse_args();spec=json.loads(args.spec.read_text())
    if spec.get('schema_version')!=1:raise ValueError('Unsupported evaluator schema version')
    effect=EFFECTS.index(spec['effect']);image=np.load(args.input,allow_pickle=False) if args.input else np.asarray(spec['samples'],dtype=np.float32)
    if args.input and image.dtype!=np.float32:raise ValueError('Input .npy must be float32; no silent image range/depth conversion')
    result=c.process(effect,image,spec.get('parameters',{}),spec.get('metadata',''))
    if args.output:np.save(args.output,result,allow_pickle=False)
    else:print(json.dumps({'schema_version':1,'effect':spec['effect'],'semantics':c.semantics(effect,spec.get('parameters',{})),'samples':result.tolist()},allow_nan=False,indent=2))
if __name__=='__main__':
    try:main()
    except (ValueError,RuntimeError) as error:sys.exit(str(error))
