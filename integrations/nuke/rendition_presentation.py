"""Host-independent, read-only presentation policy. No Nuke or color-core import."""
import json
from pathlib import Path
SCHEMA=json.loads(Path(__file__).with_name('presentation-schema.json').read_text())
GROUPS=SCHEMA['groups']
def evaluate(expr,value):
    if not isinstance(expr,list):return expr
    op,*a=expr
    if op=='predicate':return evaluate(SCHEMA['predicates'][a[0]],value)
    if op=='value':return value(a[0],a[1])
    if op=='eq':return evaluate(a[0],value)==evaluate(a[1],value)
    if op=='ne':return evaluate(a[0],value)!=evaluate(a[1],value)
    if op=='not':return not evaluate(a[0],value)
    if op=='all':return all(evaluate(x,value) for x in a)
    if op=='any':return any(evaluate(x,value) for x in a)
    if op=='min':return min(evaluate(x,value) for x in a)
    if op=='max':return max(evaluate(x,value) for x in a)
    raise ValueError('Unknown presentation predicate: '+op)
def dependencies(expr):
    if not isinstance(expr,list):return set()
    if expr[0]=='predicate':return dependencies(SCHEMA['predicates'][expr[1]])
    if expr[0]=='value':return {expr[1]}
    return set().union(*(dependencies(x) for x in expr[1:]))
def watched(effect):
    keys={'modelVersion','editFamily'}
    for c in effect['controls']:
        for field in ('enabled','native_enabled','visible','native_secret','display_range'):
            expr=c.get(field,[] if field=='display_range' else True)
            if field=='display_range':
                for x in expr:keys.update(dependencies(x))
            else:keys.update(dependencies(expr))
    return tuple(sorted(keys & {c['id'] for c in effect['controls']}))
def state(effect,value):
    """Evaluated flags/ranges only; immutable input values are never rewritten."""
    return {c['id']:{'enabled':bool(evaluate(c['enabled'],value)),
            'visible':bool(evaluate(c['visible'],value)),
            'range':tuple(evaluate(x,value) for x in c['display_range']) if 'display_range' in c else None}
            for c in effect['controls']}
