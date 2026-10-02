"""Install this development candidate into the current user's Nuke startup paths.
Preserves existing init.py text and makes a backup before adding one named block.
Does not touch system OFX plugins or the user's other menu registrations.
"""
from pathlib import Path
import argparse,shutil

root=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--home',type=Path,default=Path.home());args=parser.parse_args()
bundle=root/'build/Rendition.ofx.bundle'
if not bundle.exists():bundle=root/'Rendition.ofx.bundle'
if not (bundle/'Contents/MacOS/Rendition.ofx').is_file():raise SystemExit('Build Rendition first')
plugins=args.home/'Library/OFX/Plugins';plugins.mkdir(parents=True,exist_ok=True)
installed=plugins/bundle.name
shutil.copytree(bundle,installed,dirs_exist_ok=True)
nuke_dir=args.home/'.nuke';folder=nuke_dir/'Rendition';folder.mkdir(parents=True,exist_ok=True)
for source in (root/'integrations/nuke').glob('*.py'):
    shutil.copy2(source,folder/source.name)
# init.py also adds the bundle's parent to Nuke's plugin path. Native OFX search
# path handling varies by host; this registration is verified in the GUI.
init=nuke_dir/'init.py';old=init.read_text() if init.exists() else ''
marker='# BEGIN Rendition OFX integration'
if marker not in old:
    if init.exists():shutil.copy2(init,nuke_dir/'init.py.before-rendition')
    block="\n\n"+marker+"\nimport nuke\nnuke.pluginAddPath('Rendition')\nnuke.pluginAddPath("+repr(str(plugins))+ ")\n# END Rendition OFX integration\n"
    init.write_text(old+block)
print('Installed bundle:',installed);print('Registered menu:',folder/'menu.py');print('Restart Nuke to load the menu and bundle.')
