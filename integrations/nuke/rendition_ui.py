"""Single Nuke presentation adapter. OFX parameters remain the only grade state.
The declarative policy module owns layout/dependencies; this file owns Nuke APIs.
"""
import nuke
from pathlib import Path
import rendition_presentation as policy
_SCHEMA=policy.GROUPS  # Historical integration clients enumerate real parameter IDs.
_busy=False
_ui_signatures={}
_family_links={}

def _value(node,key,default=0):
    knob=node.knobs().get(key)
    return knob.getValue() if knob is not None else default

def _effect(node):
    # Nuke can deliver teardown callbacks after detaching the Python node wrapper.
    try:return policy.SCHEMA['effects'].get(node.Class())
    except ValueError:return None

def _add_link(node,alias,source,control,caption=None,editor=None):
    """One direct-link editor implementation, including all matrix presentations."""
    target=node.knobs().get(source)
    if target is None:return
    if control.get('no_slider'):target.clearFlag(0x2)
    if alias in node.knobs():return
    link=nuke.Link_Knob(alias,control['caption'] if caption is None else caption)
    node.addKnob(link)
    link.makeLink('this',source)
    matrix=control.get('matrix')
    if matrix:
        if not editor or not editor.get('matrix_slider',False):link.clearFlag(0x2)
        if matrix['column']!=0:link.clearFlag(nuke.STARTLINE)
    if not editor:
        for flag in control.get('bank_link_flags',[]):link.clearFlag(flag)

def update(node):
    effect=_effect(node)
    if effect is None:return
    value=lambda key,default=0:_value(node,key,default)
    flags=policy.state(effect,value)
    for c in effect['controls']:
        key=c['id'];target=node.knobs().get(key)
        if target is None:continue
        link=node.knobs().get('renditionUi_'+key)
        state=flags[key]
        if c.get('apply_enabled',True):target.setEnabled(state['enabled'])
        if link is not None:
            if c.get('apply_enabled',True):link.setEnabled(state['enabled'])
            link.setVisible(state['visible'])
        elif c['group']=='Artist':target.setVisible(state['visible'])
        if state['range'] is not None:target.setRange(*state['range'])
    family=effect['family_editor']
    if family:
        index=int(value(family['selector']))
        if _family_links.get(node.fullName())!=index:
            for suffix in family['ids']:
                link=node.knobs().get(family['alias_prefix']+suffix)
                if link is not None:link.makeLink('this',family['prefix'].format(index=index)+suffix)
            _family_links[node.fullName()]=index
        for suffix in family['ids']:
            link=node.knobs().get(family['alias_prefix']+suffix)
            source=node.knobs().get(family['prefix'].format(index=index)+suffix)
            if link is not None and source is not None:link.setEnabled(source.enabled())
    status=node.knobs().get('renditionUi_compatibility')
    if status is not None:
        key='Base' if effect['name']=='Base' else str(int(value('modelVersion')))
        status.setValue(effect['compatibility_status'].get(key,'Unsupported compatibility generation'))
    migrate=node.knobs().get('renditionUi_enableFullControls')
    if migrate is not None:migrate.setVisible(flags['enableFullControls']['visible'])

def _layout(node,effect):
    marker=policy.SCHEMA['layout_marker']
    if marker not in node.knobs():
        for knob in list(node.allKnobs()):
            if knob.name().startswith(('renditionUi_','renditionUiTab_')):node.removeKnob(knob)
    for knob in node.allKnobs():
        if knob.Class()=='Tab_Knob' and not knob.name() and knob.label()!='Node':knob.setVisible(False)
    for group,keys in _SCHEMA[node.Class()].items():
        native=node.knobs().get(group)
        if native is not None:
            native.setVisible(group=='Artist')
            if group=='Artist':native.setLabel('Main')
        for key in keys:
            target=node.knobs().get(key)
            if target is not None:target.setVisible(group=='Artist')
    controls={c['id']:c for c in effect['controls']}
    for page in effect['pages']:
        if not page['ids']:continue
        label=page['label'];tab='renditionUiTab_'+label.replace(' / ','_').replace(' ','_').replace('-','_')
        if tab not in node.knobs():node.addKnob(nuke.Tab_Knob(tab,label))
        if label=='Input / Compatibility' and 'renditionUi_compatibility' not in node.knobs():node.addKnob(nuke.Text_Knob('renditionUi_compatibility','Compatibility',''))
        for key in page['ids']:
            if key=='semanticReference':continue
            target=node.knobs().get(key)
            if target is None:continue
            target.setVisible(False)
            _add_link(node,'renditionUi_'+key,key,controls[key])
        family=effect['family_editor']
        if family and label=='Families':
            for suffix in family['ids']:
                source=family['prefix'].format(index=0)+suffix
                _add_link(node,family['alias_prefix']+suffix,source,controls[source],editor=family)
    for key in effect['hidden_links']:
        alias='renditionUi_Channel_'+key
        _add_link(node,alias,key,controls[key],caption='')
        if alias in node.knobs():node[alias].setVisible(False)
    if marker not in node.knobs():
        knob=nuke.Text_Knob(marker,'','');knob.setVisible(False);node.addKnob(knob)
    if effect['family_editor']:_family_links.pop(node.fullName(),None)

def refresh(node=None):
    global _busy
    if _busy:return
    _busy=True
    try:
        for item in ([node] if node is not None else nuke.allNodes(recurseGroups=True)):
            if item.Class() not in _SCHEMA:continue
            effect=_effect(item)
            if effect is None:
                import rendition_legacy_ui
                rendition_legacy_ui.refresh(item)
                continue
            _layout(item,effect);update(item)
    except ValueError as error:nuke.tprint('Rendition UI presentation: '+str(error))
    finally:_busy=False

def idle_update():
    global _busy
    if _busy:return
    for node in nuke.allNodes(recurseGroups=True):
        effect=_effect(node)
        if effect is None or policy.SCHEMA['layout_marker'] not in node.knobs():continue
        signature=(nuke.frame(),)+tuple(_value(node,key) for key in policy.watched(effect))
        if _ui_signatures.get(node.fullName())==signature:continue
        _ui_signatures[node.fullName()]=signature
        _busy=True
        try:update(node)
        finally:_busy=False

def created():refresh(nuke.thisNode())
def changed():
    global _busy
    if _busy:return
    node=nuke.thisNode();effect=_effect(node)
    if effect is None:return
    key=nuke.thisKnob().name()
    family=effect['family_editor']
    if family and key.startswith(family['alias_prefix']):key=family['prefix'].format(index=int(_value(node,family['selector'])))+key[len(family['alias_prefix']):]
    elif key.startswith('renditionUi_'):key=key[len('renditionUi_'):]
    if key not in ('showPanel','inputChange') and key not in policy.watched(effect):return
    _busy=True
    try:update(node)
    except ValueError:return
    finally:_busy=False

if not Path(__file__).with_name('native-ui-probe').exists():
    nuke.addOnCreate(created)
    nuke.addOnScriptLoad(refresh)
    nuke.addKnobChanged(changed)
    nuke.addUpdateUI(idle_update)
    refresh()
