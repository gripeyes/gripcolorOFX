"""Run only the named unresolved-property diagnostics; no literature discovery."""
import argparse,json
from . import volume,hk,range_tests,stacks,hub
from .common import OUT
MODULES={'volume':volume.run,'hk':hk.run,'range':range_tests.run,'stacks':stacks.run,'images':hub.run_images}
def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--modules',default='volume,hk,range,stacks,images',help='Comma-separated: volume,hk,range,stacks,images');args=parser.parse_args()
    selected=args.modules.split(',')
    if any(key not in MODULES for key in selected):parser.error('Unknown diagnostic module')
    for key in selected:print('Running',key,flush=True);MODULES[key]()
    print('Inspector Lab:',hub.build_index(),flush=True)
if __name__=='__main__':main()
