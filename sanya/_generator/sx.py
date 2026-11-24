"""Minimal S-expression tools for KiCad files."""
import os, re

KSHARE = r"C:\Program Files\KiCad\10.0\share\kicad"


class Q(str):
    """quoted string"""


def parse(text):
    tok = re.compile(r'\(|\)|"(?:\\.|[^"\\])*"|[^\s()"]+')
    stack = [[]]
    for m in tok.finditer(text):
        t = m.group(0)
        if t == '(':
            stack.append([])
        elif t == ')':
            x = stack.pop()
            stack[-1].append(x)
        elif t[0] == '"':
            stack[-1].append(Q(t[1:-1]))
        else:
            stack[-1].append(t)
    return stack[0][0]


def dump(x, ind=0):
    if isinstance(x, Q):
        return '"' + x + '"'
    if isinstance(x, str):
        return x
    if all(not isinstance(i, list) for i in x):
        return '(' + ' '.join(dump(i) for i in x) + ')'
    pad = '\t' * (ind + 1)
    out = '(' + dump(x[0])
    i = 1
    while i < len(x) and not isinstance(x[i], list):
        out += ' ' + dump(x[i])
        i += 1
    for c in x[i:]:
        out += '\n' + pad + dump(c, ind + 1)
    out += '\n' + '\t' * ind + ')'
    return out


def find(x, key):
    return [c for c in x if isinstance(c, list) and c and c[0] == key]


def first(x, key):
    r = find(x, key)
    return r[0] if r else None


_libcache = {}


def load_lib(lib):
    if lib not in _libcache:
        p = os.path.join(KSHARE, 'symbols', lib + '.kicad_sym')
        _libcache[lib] = parse(open(p, encoding='utf-8').read())
    return _libcache[lib]


def get_symbol(lib, name):
    """Return flattened symbol (extends resolved) named 'lib:name'."""
    L = load_lib(lib)
    syms = {s[1]: s for s in find(L, 'symbol')}
    s = syms[name]
    ext = first(s, 'extends')
    if ext:
        import copy
        parent = copy.deepcopy(get_symbol_raw(lib, ext[1], syms))
        pname = parent[1]
        # override properties
        cprops = {p[1]: p for p in find(s, 'property')}
        new = []
        for c in parent:
            if isinstance(c, list) and c[0] == 'property' and c[1] in cprops:
                new.append(cprops.pop(c[1]))
            elif isinstance(c, list) and c[0] == 'symbol':
                c[1] = Q(name + c[1][len(pname):])
                new.append(c)
            else:
                new.append(c)
        s = new
    else:
        import copy
        s = copy.deepcopy(s)
    s[1] = Q(lib + ':' + name)
    return s


def get_symbol_raw(lib, name, syms):
    s = syms[name]
    ext = first(s, 'extends')
    if ext:
        import copy
        parent = copy.deepcopy(get_symbol_raw(lib, ext[1], syms))
        pname = parent[1]
        cprops = {p[1]: p for p in find(s, 'property')}
        new = []
        for c in parent:
            if isinstance(c, list) and c[0] == 'property' and c[1] in cprops:
                new.append(cprops.pop(c[1]))
            elif isinstance(c, list) and c[0] == 'symbol':
                c[1] = Q(name + c[1][len(pname):])
                new.append(c)
            else:
                new.append(c)
        new[1] = Q(name)
        return new
    return s


def pins(sym):
    """list of dict(num,name,x,y,ang,len,type,unit)"""
    out = []
    for sub in find(sym, 'symbol'):
        m = re.match(r'.*_(\d+)_(\d+)$', sub[1])
        unit = int(m.group(1))
        for p in find(sub, 'pin'):
            at = first(p, 'at')
            out.append(dict(num=str(first(p, 'number')[1]), name=str(first(p, 'name')[1]),
                            x=float(at[1]), y=float(at[2]), ang=int(float(at[3])) if len(at) > 3 else 0,
                            len=float(first(p, 'length')[1]), type=p[1], unit=unit,
                            hide=any(isinstance(c, list) and c[0] == 'hide' for c in p) or 'hide' in p))
    return out


if __name__ == '__main__':
    import sys
    for a in sys.argv[1:]:
        lib, name = a.split(':')
        s = get_symbol(lib, name)
        print('==', a, 'fp:', [p[2] for p in find(s, 'property') if p[1] == 'Footprint'])
        for p in sorted(pins(s), key=lambda p: (len(p['num']), p['num'])):
            print('  %3s %-22s (%7.2f,%7.2f) a%-3d %-14s u%d %s' % (p['num'], p['name'], p['x'], p['y'], p['ang'], p['type'], p['unit'], 'HID' if p['hide'] else ''))
