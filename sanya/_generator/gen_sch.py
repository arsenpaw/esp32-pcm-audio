import math, uuid, sys, os, json
import sx
from design import C, BLOCKS, POWER, NC, U

PROJ = 'Industry_PCB'
OUT = sys.argv[1]
NS = uuid.UUID('6f1d0c1e-0000-4000-8000-000000000001')
ROOT = str(uuid.uuid5(NS, 'root'))
_n = [0]


def uid(tag=None):
    _n[0] += 1
    return str(uuid.uuid5(NS, tag or 'auto%d' % _n[0]))


def r(v):
    return round(v + 0.0, 4)


def xf(px, py, rot):
    """lib (y-up) vector -> sheet (y-down) vector for symbol rotation rot (CCW)."""
    x, y = px, -py
    t = math.radians(rot)
    c, s = round(math.cos(t)), round(math.sin(t))
    return (x * c + y * s, -x * s + y * c)


items = []
libsyms = {}
pwr_n = [0]


def need(libid):
    if libid not in libsyms:
        lib, name = libid.split(':')
        libsyms[libid] = sx.get_symbol(lib, name)
    return libsyms[libid]


def eff(size=1.27, just=None):
    return '(effects (font (size %g %g))%s)' % (size, size, (' (justify %s)' % just) if just else '')


def prop(name, val, x, y, ang=0, hide=False, just=None):
    return '(property "%s" "%s" (at %g %g %d)%s (show_name no) (do_not_autoplace no) %s)' % (
        name, val, r(x), r(y), ang, ' (hide yes)' if hide else '', eff(just=just))


def wire(a, b):
    if abs(a[0] - b[0]) < 1e-6 and abs(a[1] - b[1]) < 1e-6:
        return
    items.append('(wire (pts (xy %g %g) (xy %g %g)) (stroke (width 0) (type default)) (uuid "%s"))' % (
        r(a[0]), r(a[1]), r(b[0]), r(b[1]), uid()))


def label(name, p, d):
    ang = {(1, 0): 0, (-1, 0): 180, (0, -1): 90, (0, 1): 270}[d]
    just = {0: 'left bottom', 180: 'right bottom', 90: 'left bottom', 270: 'right bottom'}[ang]
    items.append('(label "%s" (at %g %g %d) (effects (font (size 1.27 1.27)) (justify %s)) (uuid "%s"))' % (
        name, r(p[0]), r(p[1]), ang, just, uid()))


SYMT = '''(symbol (lib_id "%s") (at %g %g %d) (unit 1) (body_style 1) (exclude_from_sim no) (in_bom %s) (on_board %s) (in_pos_files yes) (dnp no) (uuid "%s")
%s
%s
 (instances (project "%s" (path "/%s" (reference "%s") (unit 1)))))'''


def power(name, p, flip=False, rot=None):
    pwr_n[0] += 1
    ref = '#PWR%03d' % pwr_n[0]
    libid = 'power:' + name
    need(libid)
    isg = name == 'GND'
    dy = (6.35 if isg else -3.81) * (-1 if flip else 1)
    props = '\n'.join([
        prop('Reference', ref, p[0], p[1] + 2.54, hide=True),
        prop('Value', name, p[0], p[1] + dy, hide=isg),
        prop('Footprint', '', p[0], p[1], hide=True), prop('Datasheet', '', p[0], p[1], hide=True),
        prop('Description', 'Power symbol', p[0], p[1], hide=True)])
    items.append(SYMT % (libid, r(p[0]), r(p[1]), rot if rot is not None else (180 if flip else 0), 'yes', 'yes', uid('pwr' + ref), props,
                         ' (pin "1" (uuid "%s"))' % uid(), PROJ, ROOT, ref))


def flag(p):
    pwr_n[0] += 1
    ref = '#FLG%03d' % pwr_n[0]
    need('power:PWR_FLAG')
    props = '\n'.join([
        prop('Reference', ref, p[0], p[1] - 2, hide=True), prop('Value', 'PWR_FLAG', p[0], p[1] - 5.08),
        prop('Footprint', '', p[0], p[1], hide=True), prop('Datasheet', '', p[0], p[1], hide=True),
        prop('Description', 'Power flag', p[0], p[1], hide=True)])
    items.append(SYMT % ('power:PWR_FLAG', r(p[0]), r(p[1]), 0, 'yes', 'yes', uid('flg' + ref), props,
                         ' (pin "1" (uuid "%s"))' % uid(), PROJ, ROOT, ref))


SYM_UUID = {}
NETS = {}


def resolve(ref, spec):
    c = C[ref]
    if isinstance(spec, tuple) and spec[0] == 'JOIN':
        return resolve(ref, c['pins'][spec[1]])
    if isinstance(spec, tuple):
        return spec[0]
    return spec


def place(ref):
    c = C[ref]
    sym = need(c['lib'])
    X, Y, rot = c['at'][0] * U, c['at'][1] * U, c['rot']
    plist = sx.pins(sym)
    ends = {}
    for p in plist:
        ex, ey = xf(p['x'], p['y'], rot)
        a = math.radians(p['ang'])
        dx, dy = xf(-round(math.cos(a)), -round(math.sin(a)), rot)
        ends[p['num']] = ((X + ex, Y + ey), (int(round(dx)), int(round(dy))), p)
    xs, ys = [], []
    for num, (pos, d, p) in ends.items():
        xs.append(pos[0] - d[0] * p['len'])
        ys.append(pos[1] - d[1] * p['len'])
    if not xs:
        xs, ys = [X - 2, X + 2], [Y - 2, Y + 2]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    np_ = len([p for p in plist if not p['hide']])
    name = c['lib'].split(':')[1]
    fa, j = 0, None
    if name == 'TestPoint':
        rp, vp = (X, Y - 5.6), (X, Y - 3.9)
    elif name == 'MountingHole':
        rp, vp = (X, Y - 3.4), (X, Y + 3.4)
    elif name == 'SW_Push':
        rp, vp = (X, Y - 5.6), (X, Y - 3.7)
    elif name == 'Buzzer':
        rp, vp, j = (X + 4.5, Y - 1.27), (X + 4.5, Y + 1.27), 'left'
    elif name.startswith('Conn_01') or name.startswith('Screw'):
        rp, vp, j = (X - 1.3, y0 - 3.6), (X - 1.3, y1 + 4.2), 'left'
    elif np_ <= 2:
        d0 = list(ends.values())[0][1]
        fa = 90 if rot in (90, 270) else 0
        if d0[1] == 0:
            rp, vp = (X, Y - (4.8 if name == 'LED' else 3.0)), (X, Y + 3.0)
        else:
            rp, vp, j = (X + 2.6, Y - 1.27), (X + 2.6, Y + 1.27), ('right' if rot in (90, 180) else 'left')
    else:
        rp, vp, j = (x0, y0 - 3.3), (x0, y0 - 1.4), 'left'
        if name == 'ATmega328P-A':
            rp, vp = (x0, y1 + 1.9), (x0, y1 + 3.8)
        if name == 'ADXL343':
            rp, vp = (x1 + 1.0, y0 + 1.5), (x1 + 1.0, y0 + 3.4)
        if name == 'ULN2003A':
            rp, vp = (x0, y0 - 5.2), (x0, y0 - 3.3)
        if name == 'AVR-ISP-6':
            rp, vp = (X + 2.5, y0 - 3.3), (X + 2.5, y0 - 1.4)
        if name == 'SANYOU_SRD_Form_C':
            rp, vp = (x1 + 3.5, Y - 1.27), (x1 + 3.5, Y + 1.27)
        if name == 'R_Pack04':
            rp, vp = (x1 + 2.0, Y - 1.27), (x1 + 2.0, Y + 1.27)
        if name in ('L7805', 'MCP1700x-330xxTT'):
            rp, vp = (X - 3.8, Y - 4.8), (X + 1.6, Y + 6.6)
        if name == 'BAT54S':
            rp, vp = (X - 3, y0 - 4.6), (X - 3, y0 - 2.8)
    u = uid('sym' + ref)
    SYM_UUID[ref] = u
    props = '\n'.join([
        prop('Reference', ref, rp[0], rp[1], fa, just=j),
        prop('Value', c['val'], vp[0], vp[1], fa, just=j, hide=(name == 'TestPoint')),
        prop('Footprint', c['fp'], X, Y, hide=True),
        prop('Datasheet', '', X, Y, hide=True),
        prop('Description', '', X, Y, hide=True)] + ([prop('MPN', c['mpn'], X, Y, hide=True), prop('Manufacturer', c['mfr'], X, Y, hide=True)] if c['mpn'] else []))
    pinl = '\n'.join(' (pin "%s" (uuid "%s"))' % (p['num'], uid()) for p in plist)
    items.append(SYMT % (c['lib'], r(X), r(Y), rot, 'yes' if c['bom'] else 'no', 'yes', u, props, pinl, PROJ, ROOT, ref))
    stub_end = {}
    for num, spec in c['pins'].items():
        pos, d, p = ends[num]
        net = resolve(ref, spec)
        if net == NC:
            items.append('(no_connect (at %g %g) (uuid "%s"))' % (r(pos[0]), r(pos[1]), uid()))
            continue
        NETS.setdefault(net, []).append((ref, num))
        for q in plist:
            if q['num'] != num and q['hide'] and q['type'] != 'no_connect' and abs(q['x'] - p['x']) < 1e-6 and abs(q['y'] - p['y']) < 1e-6:
                NETS[net].append((ref, q['num']))
        ln, opt = U, None
        if isinstance(spec, tuple) and spec[0] != 'JOIN':
            ln = spec[1] * U
            opt = spec[2] if len(spec) > 2 else None
        e = (pos[0] + d[0] * ln, pos[1] + d[1] * ln)
        stub_end[num] = e
        wire(pos, e)
        if isinstance(spec, tuple) and spec[0] == 'JOIN':
            continue
        if net in POWER:
            if d[1] == 0 and opt == 'side':
                power(net, e, rot=270 if d[0] < 0 else 90)
            elif d[1] == 0:
                l2 = (opt or 1) * U
                e2 = (e[0], e[1] + (l2 if net == 'GND' else -l2))
                wire(e, e2)
                power(net, e2)
            elif (d[1] > 0) == (net == 'GND'):
                power(net, e)
            else:
                power(net, e, flip=True)
        else:
            label(net, e, d)
    for num, spec in c['pins'].items():
        if isinstance(spec, tuple) and spec[0] == 'JOIN':
            wire(stub_end[num], stub_end[spec[1]])


for ref in C:
    place(ref)

for i, net in enumerate(['+12V', 'GND']):
    p = ((103 + 4 * i) * U, 17 * U)
    e = (p[0], p[1] + U)
    flag(p)
    wire(p, e)
    power(net, e, flip=(net != 'GND'))
p = (79 * U, 34 * U)
flag(p)
wire(p, (p[0], p[1] + U))
label('+3V3A', (p[0], p[1] + U), (0, 1))

for title, (x0, y0, x1, y1) in BLOCKS.items():
    items.append('(rectangle (start %g %g) (end %g %g) (stroke (width 0.2) (type dash)) (fill (type none)) (uuid "%s"))' % (
        r(x0 * U), r(y0 * U), r(x1 * U), r(y1 * U), uid()))
    items.append('(text "%s" (exclude_from_sim no) (at %g %g 0) (effects (font (size 1.8 1.8) (bold yes)) (justify left bottom)) (uuid "%s"))' % (
        title, r(x0 * U + 1.5), r(y0 * U + 3.6), uid()))

NOTES = [
    (116, 24.4, 'Programmer must be set to 3.3V target (ADXL345 abs. max 3.9V)'),
    (66, 65.4, 'Vadc = Vin*18k/(10k+18k): 5.0V -> 3.21V; fc ~ 250Hz; BAT54S clamps to GND/3V3'),
    (116, 45.4, 'J3: 1=VDD(3V3) 2=DQ 3=GND; 4.7k pull-up = RN2 (pins 3-6)'),
    (116, 65.4, 'J5: 1=GND 2=VCC 3=SCL 4=SDA (0.96in SSD1306 module)'),
    (54, 91.4, 'IN1=relay IN2=buzzer IN3-5=fan (3 ch. parallel); COM=+12V clamp'),
    (96, 91.4, 'Relay energised = NORMAL (fail-safe): load via COM-NO'),
    (137, 91.4, 'Fan <= 0.6A, PWM on PD3 (OC2B)'),
    (6, 65.4, 'I2C / 1-Wire / RESET pull-ups: RN2 4x4.7k to 3V3'),
    (66, 45.4, 'CS=VDDIO -> I2C mode; SDO=GND -> addr 0x53; INT1 -> PD2/INT0'),
    (6, 91.4, 'D7 (relay state LED) is fed from RELAY_CTRL via RN1 (pins 4-5)'),
]
for x, y, t in NOTES:
    items.append('(text "%s" (exclude_from_sim no) (at %g %g 0) (effects (font (size 1.1 1.1) (italic yes)) (justify left bottom)) (uuid "%s"))' % (
        t, r(x * U), r(y * U), uid()))

lib = '\n'.join(sx.dump(s, 2) for s in libsyms.values())
doc = '''(kicad_sch
	(version 20260306)
	(generator "eeschema")
	(generator_version "10.0")
	(uuid "%s")
	(paper "A3")
	(title_block
		(title "Engine condition monitor: vibration, temperature, pressure")
		(date "2026-11-16")
		(rev "2.0")
		(company "Educational prototype - not certified for vehicle use")
	)
	(lib_symbols
		%s
	)
%s
	(sheet_instances
		(path "/"
			(page "1")
		)
	)
	(embedded_fonts no)
)
''' % (ROOT, lib, '\n'.join('\t' + i for i in items))
open(OUT, 'w', encoding='utf-8', newline='\n').write(doc)
json.dump({'nets': NETS, 'uuid': SYM_UUID, 'root': ROOT},
          open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'design_nets.json'), 'w'), indent=1)
print('symbols', len(C), 'nets', len(NETS))
