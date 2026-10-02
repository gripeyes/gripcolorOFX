"""Resolve the project's scene_linear role for Auto; never choose creative math.
The OFX reads the derived nonpersistent bridge parameter in its render snapshot.
Nuke's built-in PyOpenColorIO handles config includes, aliases and built-in URIs.
"""
import nuke
import PyOpenColorIO as ocio

PREFIX = 'OFXorg.gripcolor.rendition.'
SPACE_CODES = {
    'lin_rec2020': 2, 'Linear Rec.2020': 2, 'Linear Rec.2020 (D65)': 2,
    'ACEScg': 3, 'ACES - ACEScg': 3,
    'lin_rec709_srgb': 4, 'Linear Rec.709': 4, 'Linear Rec.709 (sRGB)': 4,
}
_busy = False

def resolve_scene_linear():
    """1 means unavailable/unsupported; 0 is reserved for no host bridge."""
    root = nuke.root()
    try:
        if root['colorManagement'].value() != 'OCIO':
            return 1, 'scene_linear requires an OCIO project; select manual interpretation'
        path = root['OCIOConfigPath'].value()
        if root['OCIO_config'].value() == 'custom':
            path = root['customOCIOConfigPath'].value()
        config = ocio.Config.CreateFromFile(path)
        if not config.hasRole('scene_linear'):
            return 1, 'OCIO scene_linear role is missing; interpretation required'
        space = config.getColorSpace('scene_linear')
        if space is None or space.isData():
            return 1, 'OCIO scene_linear role is invalid; interpretation required'
        names = [space.getName(), *space.getAliases()]
        codes = {SPACE_CODES[name] for name in names if name in SPACE_CODES}
        if len(codes) != 1:
            return 1, 'Unsupported/ambiguous scene_linear: '+space.getName()+'; select manual interpretation'
        return codes.pop(), 'Auto uses scene_linear: '+space.getName()+'; manual selection overrides'
    except Exception as error:
        return 1, 'Cannot resolve scene_linear: '+str(error)+'; interpretation required'

def refresh(node=None):
    global _busy
    if _busy:
        return
    _busy = True
    try:
        code, status = resolve_scene_linear()
        nodes = [node] if node is not None else nuke.allNodes(recurseGroups=True)
        for item in nodes:
            if not item.Class().startswith(PREFIX) or 'hostSceneLinear' not in item.knobs():
                continue
            knob = item['hostSceneLinear']
            if knob.getValue() != code:
                knob.setValue(code)
            item['interpretation'].setTooltip(status+'. Interpretation only; no pixel conversion or look change.')
    finally:
        _busy = False

def on_create():
    refresh(nuke.thisNode())

def on_knob_changed():
    node = nuke.thisNode()
    knob = nuke.thisKnob()
    if node.Class() == 'Root' and knob.name() in ('colorManagement', 'OCIO_config', 'customOCIOConfigPath', 'OCIOConfigPath'):
        refresh()
    elif node.Class().startswith(PREFIX) and knob.name() == 'interpretation':
        refresh(node)

nuke.addOnCreate(on_create)
nuke.addOnScriptLoad(refresh)
nuke.addKnobChanged(on_knob_changed)
nuke.addBeforeRender(refresh)
