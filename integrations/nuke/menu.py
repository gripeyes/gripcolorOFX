"""Normal Nuke menu/Tab-search exposure for the native Rendition OFX nodes.
No processing math, implicit gamut selection or extra grading knobs live here.
"""
import nuke

EFFECTS = ('Scene', 'Tone', 'Volume', 'Density', 'Crossover', 'Crosstalk', 'Strip', 'Inspector', 'Primaries')
menus = [nuke.menu('Nodes').addMenu('Rendition', icon='Color.png'),
         nuke.menu('Nuke').addMenu('Rendition')]
for effect in EFFECTS:
    # Standard menu command strings participate in Nuke's node-search index.
    for menu in menus:
        menu.addCommand(effect, "nuke.createNode('OFXorg.gripcolor.rendition.%s_v1')" % effect)

menus[1].addSeparator()
menus[1].addCommand('Quick Help', lambda: nuke.message(
    'Rendition CPU artist build\n\n'
    'Auto uses your OCIO scene_linear role. Missing or unsupported roles require manual Source interpretation. '
    'Manual interpretation identifies incoming RGB; it does not convert gamut.\n\n'
    'Default controls copy RGB and alpha exactly. RGB as supplied is the default. '
    'Optional unpremultiply/process/premultiply retains zero-alpha RGB.\n\n'
    'Primaries: direct master/blacks/midtones/whites colour and soft ranges. Scene: exposure/illuminant/SOP. Tone: tonal relationships. Volume: six continuous families. '
    'Density: depth/chroma candidate. Crossover: exposure-evolving colour. '
    'Crosstalk: inspectable matrix. Strip: separation/palette candidate. Inspector: diagnostics.\n\n'
    'Density and Strip remain research candidates. Basic usability is accepted; aggressive-range simplicity challenges remain open. '
    'Flame and host Metal are separate pending gates.'))


def inspector_lab():
    from pathlib import Path
    import webbrowser
    pointer = Path(__file__).with_name('inspector-lab-path.txt')
    path = Path(pointer.read_text().strip()) if pointer.exists() else None
    if path is not None and path.is_file():
        webbrowser.open(path.as_uri())
    else:
        nuke.message('Generate Inspector Lab reports in the repository:\nPYTHONPATH=build .venv/bin/python -m diagnostics.run')

menus[1].addCommand('Inspector Lab / Diagnostic Reports', inspector_lab)

def primaries_examples():
    from pathlib import Path
    import webbrowser
    pointer=Path(__file__).with_name('primaries-path.txt')
    path=Path(pointer.read_text().strip()) if pointer.exists() else None
    if path is not None and path.is_file():webbrowser.open(path.as_uri())
    else:nuke.message('Artist Primaries examples are not installed; see docs/ARTIST_PRIMARIES.md.')

menus[1].addCommand('Artist Primaries / Examples', primaries_examples)
