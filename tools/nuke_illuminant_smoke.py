"""Targeted Nuke host check for the appended Base illuminant controls."""
import json
import math
import sys
from pathlib import Path
import nuke

ROOT = Path(__file__).resolve().parents[1]
old = sys.modules.get('rendition_ui')
if old is not None:
    for remove, name in (('removeOnCreate', 'created'), ('removeOnScriptLoad', 'refresh'),
                         ('removeKnobChanged', 'changed'), ('removeUpdateUI', 'idle_update')):
        getattr(nuke, remove)(getattr(old, name))
for module in ('rendition_ui', 'rendition_presentation'):
    sys.modules.pop(module, None)
sys.path.insert(0, str(ROOT / 'integrations/nuke'))
import rendition_ui as ui

out = ROOT / 'build/illuminant'
out.mkdir(parents=True, exist_ok=True)
source = nuke.nodes.Constant(name='IlluminantSource')
source['format'].setValue('square_256')
source['color'].setValue([.18, .18, .18, .37])
base = nuke.createNode('OFXorg.gripcolor.rendition.Base_v1', inpanel=False)
base.setName('IlluminantBase')
base.setInput(0, source)
base['interpretation'].setValue(1)
ui.refresh(base)
assert base['temperature'].getValue() == 6504
assert base['illuminantVersion'].getValue() == 1
assert base['illuminantTint'].getValue() == 0
for key in ('temperature', 'illuminantTint', 'illuminantAdaptation'):
    # In terminal Nuke visible() is false without a GUI widget; inspect the presentation flag.
    assert not base['renditionUi_' + key].getFlag(nuke.INVISIBLE)
assert base['renditionUi_illuminantVersion'].getFlag(nuke.INVISIBLE)
assert not base['illuminantAdaptation'].enabled()

def sample(node):
    result = [node.sample(ch, 100.5, 100.5, frame=nuke.frame()) for ch in ('red', 'green', 'blue', 'alpha')]
    assert all(math.isfinite(v) for v in result)
    assert abs(result[3] - .37) < 1e-6
    return result

neutral = sample(base)
assert all(abs(a-b) < 1e-6 for a,b in zip(neutral, [.18,.18,.18,.37]))
base['renditionUi_temperature'].setValue(6000)
ui.update(base)
assert base['temperature'].getValue() == 6000
assert base['illuminantAdaptation'].enabled()
cool = sample(base)
base['renditionUi_temperature'].setValue(6500)
warm = sample(base)
assert cool[0] < warm[0] and cool[2] > warm[2]
base['temperature'].setAnimated()
base['temperature'].setValueAt(6000, 1)
base['temperature'].setValueAt(6500, 2)
samples = {}
for frame in (1, 2):
    nuke.frame(frame)
    ui.update(base)
    samples[str(frame)] = sample(base)
    assert base['renditionUi_temperature'].valueAt(frame) == base['temperature'].valueAt(frame)
scene = nuke.createNode('OFXorg.gripcolor.rendition.Scene_v1', inpanel=False)
scene.setInput(0, source)
scene['interpretation'].setValue(1)
assert scene['illuminantVersion'].getValue() == 0
assert scene['temperature'].getValue() == 6504

nuke.scriptSaveAs(str(out / 'illuminant-smoke.nk'), overwrite=1)
nuke.scriptClear()
nuke.scriptOpen(str(out / 'illuminant-smoke.nk'))
base = nuke.toNode('IlluminantBase')
base.setName('RenamedIlluminantBase')
ui.refresh(base)
assert base['illuminantVersion'].getValue() == 1
for frame in (1, 2):
    nuke.frame(frame)
    assert base['temperature'].valueAt(frame) == (6000 if frame == 1 else 6500)
    actual = sample(base)
    assert all(abs(a-b) <= 2e-6 + 2e-5*abs(b) for a,b in zip(actual, samples[str(frame)])), (frame, actual, samples[str(frame)])
report = {'passed': True, 'host': nuke.NUKE_VERSION_STRING,
          'neutral': neutral, '6000K': cool, '6500K': warm,
          'checks': ['linked controls target real OFX state', 'neutral exact bypass',
                     'conditional adaptation enabled state', '6000/6500 render response',
                     'timed animation', 'save/reload and rename', 'Scene legacy default'],
          'scope': 'Terminal Nuke host smoke; no GUI mouse-drag acceptance claim'}
(out / 'nuke-smoke.json').write_text(json.dumps(report, indent=2) + '\n')
print('RENDITION_ILLUMINANT_SMOKE_PASS ' + json.dumps(report))
