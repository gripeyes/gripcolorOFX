"""Assemble the 0.32 UX evidence; never promote pending acceptance."""
from pathlib import Path
import html,json,re
root=Path(__file__).resolve().parents[1];out=root/'build/ux-0.32';out.mkdir(parents=True,exist_ok=True)
text=(root/'docs/NUKE_UX_0.32.md').read_text()
rows=[]
for line in text.splitlines():
 if line.startswith('| ') and line.count('|')==5:
  cols=[x.strip() for x in line.strip('|').split('|')]
  if cols[0]!='Reproduced problem':rows.append(dict(zip(('problem','cause','correction','evidence'),cols)))
result={'version':'0.32-ux-candidate','acceptance':'pending','presets':'stopped','new_node_default_promoted':False,'historical_equations':'bitwise regression passed','issues':rows,'interactive_mouse':'Material Density/Chroma Coupling maxima and all Palette Main endpoints verified; complete connected-Viewer sweep remains pending','host_checks':json.loads((out/'host-checks.json').read_text())}
(out/'audit.json').write_text(json.dumps(result,indent=2)+'\n')
def inline(s):
 s=html.escape(s)
 s=re.sub(r'\*\*(.+?)\*\*',r'<strong>\1</strong>',s)
 s=re.sub(r'`([^`]+)`',r'<code>\1</code>',s)
 return re.sub(r'\[([^]]+)\]\((https?://[^)]+)\)',r'<a href="\2">\1</a>',s)
parts=[];table=False
for line in text.splitlines():
 if line.startswith('|'):
  if not table:parts.append('<table>');table=True
  if re.match(r'^\|[- |]+\|$',line):continue
  parts.append('<tr>'+''.join('<td>'+inline(c.strip())+'</td>' for c in line.strip('|').split('|'))+'</tr>');continue
 if table:parts.append('</table>');table=False
 if line.startswith('#'):
  n=len(line)-len(line.lstrip('#'));parts.append(f'<h{n}>'+inline(line[n:].strip())+f'</h{n}>')
 elif line:parts.append('<p>'+inline(line)+'</p>')
if table:parts.append('</table>')
parts.append('<h2>Actual Nuke UI evidence</h2><p>Captured UI, not mockups. Each image links to its accessibility record. Not every screenshot proves mouse acceptance.</p>')
for p in sorted((out/'screenshots').glob('*.png')):
 if p.stem=='native-capture-test':continue
 parts.append(f'<figure><a href="screenshots/{p.stem}.txt"><img loading="lazy" src="screenshots/{p.name}"></a><figcaption>{html.escape(p.stem.replace("-"," "))}</figcaption></figure>')
(out/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>Rendition 0.32 UX correction</title><style>body{background:#181b20;color:#eee;font:16px/1.6 system-ui;max-width:1100px;margin:40px auto;padding:24px}a{color:#8dcfff}td{padding:12px;border:1px solid #48505b;vertical-align:top}table{border-collapse:collapse;width:100%}img{max-width:100%;height:auto}figure{margin:40px 0}code{color:#e9c78c}h2{margin-top:48px}</style>'+''.join(parts))
print(out/'index.html')
