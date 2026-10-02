import nuke, json
items=[str(p) for p in nuke.plugins(nuke.ALL) if 'rendition' in str(p).lower()]
print('RENDITION_DISCOVERY',json.dumps(items))
for cls in ['OFXorg.gripcolor.rendition.Scene_v1','OFXorg.gripcolor.rendition.Scene','org.gripcolor.rendition.Scene','RenditionScene']:
    try:
        node=nuke.createNode(cls,inpanel=False)
        print('CREATED',node.Class(),json.dumps(list(node.knobs())))
        break
    except Exception as e:print('CREATE_FAILED',cls,str(e))
