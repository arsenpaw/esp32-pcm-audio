"""Wired schematic generator (v2): real wires inside every functional group."""
import math, uuid, sys
import sx
from design import C

U = 2.54
PROJ = 'Industry_PCB'
OUT = sys.argv[1]
NS = uuid.UUID('6f1d0c1e-0000-4000-8000-000000000001')
ROOT = str(uuid.uuid5(NS, 'root'))
_n = [0]


def uid(tag=None):
    _n[0] += 1
    return str(uuid.uuid5(NS, tag or 'v2auto%d' % _n[0]))


def r(v):
    return round(v + 0.0, 4)


items, libsyms = [], {}
PIN = {}            # (ref, num) -> (xu, yu)
pin_pts = []        # all connected pin end points (u)
wires = []          # ((x0,y0),(x1,y1)) in u
pwr_n = [0]
LIBOVR = {'RN1': 'Device:R_Pack04_Split', 'RN2': 'Device:R_Pack04_Split'}


def need(libid):
    if libid not in libsyms:
        lib, name = libid.split(':')
        libsyms[libid] = sx.get_symbol(lib, name)
    return libsyms[libid]


def prop(name, val, x, y, ang=0, hide=False, just=None):
    return '(property "%s" "%s" (at %g %g %d)%s (show_name no) (do_not_autoplace no) (effects (font (size 1.27 1.27))%s))' % (
        name, val, r(x), r(y), ang, ' (hide yes)' if hide else '', (' (justify %s)' % just) if just else '')


SYMT = '''(symbol (lib_id "%s") (at %g %g %d)%s (unit %d) (body_style 1) (exclude_from_sim no) (in_bom %s) (on_board yes) (in_pos_files yes) (dnp no) (uuid "%s")
%s
%s
 (instances (project "%s" (path "/%s" (reference "%s") (unit %d)))))'''


def xf(px, py, rot, mirror):
    if mirror == 'y':
        px = -px
    if mirror == 'x':
        py = -py
    x, y = px, -py
    t = math.radians(rot)
    c, s = round(math.cos(t)), round(math.sin(t))
    return (x * c + y * s, -x * s + y * c)


def sym(ref, x, y, rot=0, mirror=None, unit=1, rp=None, vp=None, just=None, fa=None, hide_val=False):
    """place symbol (unit) of component ref at (x,y) u. rp/vp = absolute field positions in u."""
    c = C[ref]
    libid = LIBOVR.get(ref, c['lib'])
    s = need(libid)
    X, Y = x * U, y * U
    plist = [p for p in sx.pins(s) if p['unit'] in (0, unit)]
    for p in plist:
        ex, ey = xf(p['x'], p['y'], rot, mirror)
        PIN[(ref, p['num'])] = ((X + ex) / U, (Y + ey) / U)
    two = len([p for p in plist if not p['hide']]) <= 2
    if fa is None:
        fa = 90 if rot in (90, 270) else 0
    if rp is None or vp is None:
        ends = [PIN[(ref, p['num'])] for p in plist]
        horiz = two and len(ends) == 2 and abs(ends[0][1] - ends[1][1]) < 1e-6
        if two and horiz:
            d_rp, d_vp, dj = (x, y - 1.15), (x, y + 1.25), None
        elif two:
            d_rp, d_vp, dj = (x + 0.9, y - 0.5), (x + 0.9, y + 0.5), ('right' if rot in (90, 180) else 'left')
        else:
            d_rp, d_vp, dj = (x, y - 3), (x, y + 3), None
        rp = rp or d_rp
        vp = vp or d_vp
        if just is None:
            just = dj
    u = uid('sym' + ref) if unit == 1 else uid('sym%su%d' % (ref, unit))
    props = [prop('Reference', ref, rp[0] * U, rp[1] * U, fa, just=just),
             prop('Value', c['val'], vp[0] * U, vp[1] * U, fa, just=just, hide=hide_val),
             prop('Footprint', c['fp'], X, Y, hide=True),
             prop('Datasheet', '', X, Y, hide=True),
             prop('Description', '', X, Y, hide=True)]
    if c['mpn']:
        props += [prop('MPN', c['mpn'], X, Y, hide=True), prop('Manufacturer', c['mfr'], X, Y, hide=True)]
    pinl = '\n'.join(' (pin "%s" (uuid "%s"))' % (p['num'], uid()) for p in plist)
    items.append(SYMT % (libid, r(X), r(Y), rot, (' (mirror %s)' % mirror) if mirror else '', unit,
                         'yes' if c['bom'] else 'no', u, '\n'.join(props), pinl, PROJ, ROOT, ref, unit))


def P(ref, num):
    p = PIN[(ref, str(num))]
    if p not in pin_pts:
        pin_pts.append(p)
    return p


def W(*pts):
    pts = [p for p in pts]
    for a, b in zip(pts, pts[1:]):
        assert abs(a[0] - b[0]) < 1e-6 or abs(a[1] - b[1]) < 1e-6, ('not orthogonal', a, b)
        if abs(a[0] - b[0]) < 1e-6 and abs(a[1] - b[1]) < 1e-6:
            continue
        wires.append((a, b))


def lab(name, x, y, side='r'):
    ang, just = {'r': (0, 'left bottom'), 'l': (180, 'right bottom'), 'u': (90, 'left bottom'), 'd': (270, 'right bottom')}[side]
    items.append('(label "%s" (at %g %g %d) (effects (font (size 1.27 1.27)) (justify %s)) (uuid "%s"))' % (
        name, r(x * U), r(y * U), ang, just, uid()))


def pwr(name, x, y, rot=0):
    pwr_n[0] += 1
    ref = '#PWR%03d' % pwr_n[0]
    libid = 'power:' + name
    need(libid)
    X, Y = x * U, y * U
    isg = name == 'GND'
    props = '\n'.join([prop('Reference', ref, X, Y + 2.54, hide=True),
                       prop('Value', name, X, Y + (6.35 if isg else -3.81), hide=isg),
                       prop('Footprint', '', X, Y, hide=True), prop('Datasheet', '', X, Y, hide=True),
                       prop('Description', 'Power symbol', X, Y, hide=True)])
    items.append(SYMT % (libid, r(X), r(Y), rot, '', 1, 'yes', uid('v2pwr' + ref), props,
                         ' (pin "1" (uuid "%s"))' % uid(), PROJ, ROOT, ref, 1))
    pin_pts.append((x, y))


def flag(x, y):
    pwr_n[0] += 1
    ref = '#FLG%03d' % pwr_n[0]
    need('power:PWR_FLAG')
    X, Y = x * U, y * U
    props = '\n'.join([prop('Reference', ref, X, Y - 2, hide=True), prop('Value', 'PWR_FLAG', X, Y - 5.08),
                       prop('Footprint', '', X, Y, hide=True), prop('Datasheet', '', X, Y, hide=True),
                       prop('Description', 'Power flag', X, Y, hide=True)])
    items.append(SYMT % ('power:PWR_FLAG', r(X), r(Y), 0, '', 1, 'yes', uid('v2flg' + ref), props,
                         ' (pin "1" (uuid "%s"))' % uid(), PROJ, ROOT, ref, 1))
    pin_pts.append((x, y))


def nc(ref, num):
    p = PIN[(ref, str(num))]
    items.append('(no_connect (at %g %g) (uuid "%s"))' % (r(p[0] * U), r(p[1] * U), uid()))


def stub(ref, num, name, dx=1, side=None):
    """short stub from a pin with a net label"""
    p = P(ref, num)
    e = (p[0] + dx, p[1])
    W(p, e)
    lab(name, e[0], e[1], side or ('r' if dx > 0 else 'l'))


def text(s, x, y, size=1.1, bold=False, italic=True):
    items.append('(text "%s" (exclude_from_sim no) (at %g %g 0) (effects (font (size %g %g)%s%s) (justify left bottom)) (uuid "%s"))' % (
        s, r(x * U), r(y * U), size, size, ' (bold yes)' if bold else '', ' (italic yes)' if italic else '', uid()))


def frame(title, x0, y0, x1, y1):
    items.append('(rectangle (start %g %g) (end %g %g) (stroke (width 0.2) (type dash)) (fill (type none)) (uuid "%s"))' % (
        r(x0 * U), r(y0 * U), r(x1 * U), r(y1 * U), uid()))
    text(title, x0 + 0.6, y0 + 1.4, size=1.8, bold=True, italic=False)


GND, V12, V5, V33 = 'GND', '+12V', '+5V', '+3V3'

# =====================================================================
# 1. POWER
# =====================================================================
frame('1. POWER   12V -> fuse -> reverse-polarity diode -> TVS -> 5V -> 3.3V', 4, 6, 120, 24)
sym('J1', 10, 16, mirror='y', rp=(9.5, 14.2), vp=(9.5, 18.9))
sym('F1', 20, 16, rot=90)
sym('D1', 30, 16, rot=180)
sym('D2', 36, 17.5, rot=90)
sym('C1', 44, 17.5)
sym('TP1', 49, 16, rp=(49, 13.9), vp=(49, 13), hide_val=True)
sym('U1', 64, 16, rp=(64, 13.3), vp=(66.2, 18.6), just='left')
sym('C2', 72, 17.5)
sym('TP2', 76, 16, rp=(76, 13.9), vp=(76, 13), hide_val=True)
sym('U2', 88, 16, rp=(88, 13.3), vp=(90.2, 18.6), just='left')
sym('C3', 99, 17.5)
sym('TP3', 103, 16, rp=(103, 13.9), vp=(103, 13), hide_val=True)
sym('TP4', 116, 17, rp=(116, 14.9), vp=(116, 14), hide_val=True)
W(P('J1', 1), P('F1', 1)); lab('VIN_RAW', 13, 16)
W(P('J1', 2), (14, 17), (14, 19)); pwr(GND, 14, 19)
W(P('F1', 2), P('D1', 2)); lab('VIN_FUSED', 22, 16)
W(P('D1', 1), P('U1', 1))
pwr(GND, *P('D2', 1)); pwr(GND, *P('C1', 2))
W((53, 16), (53, 15)); pwr(V12, 53, 15)
flag(57, 16)
P('D2', 2); P('C1', 1); P('TP1', 1)
W(P('U1', 2), (64, 20)); pwr(GND, 64, 20)
W(P('U1', 3), P('U2', 3))
pwr(GND, *P('C2', 2)); P('C2', 1); P('TP2', 1)
W((80, 16), (80, 15)); pwr(V5, 80, 15)
W(P('U2', 1), (88, 20)); pwr(GND, 88, 20)
W(P('U2', 2), (107, 16), (107, 15)); pwr(V33, 107, 15)
pwr(GND, *P('C3', 2)); P('C3', 1); P('TP3', 1)
flag(112, 17); W((112, 17), (112, 18)); pwr(GND, 112, 18)
W(P('TP4', 1), (116, 18)); pwr(GND, 116, 18)
text('F1 1.1A PTC; D1 blocks reversed supply; D2 clamps surges; +12V feeds relay coil, fan and U1 only', 5, 23.4)

# mounting holes
frame('MECHANICAL', 122, 6, 160, 24)
for i, h in enumerate(['H1', 'H2', 'H3', 'H4']):
    sym(h, 128 + 8 * i, 16, rp=(128 + 8 * i, 14.2), vp=(128 + 8 * i, 17.8))
text('4 x M3 mounting holes; H4 is next to the ADXL345', 123, 23.4)

# =====================================================================
# 2. MCU + clock + reset + LEDs + button + ISP
# =====================================================================
frame('2. MCU ATmega328P-AU (3.3V, 8MHz)   7. USER INTERFACE   11. PROGRAMMING', 4, 26, 70, 82)
sym('U3', 24, 62, rp=(26, 78.2), vp=(26, 79.4), just='left')
# supply + decoupling
W(P('U3', 4), (24, 44)); pwr(V33, 24, 44)
W(P('U3', 18), (25, 46), (24, 46))
W((24, 45), (10, 45))
sym('C4', 14, 46.5); sym('C5', 10, 46.5)
P('C4', 1); P('C5', 1)
pwr(GND, *P('C4', 2)); pwr(GND, *P('C5', 2))
W(P('U3', 3), (24, 78)); pwr(GND, 24, 78)
for n in (20, 19, 22, 24, 25, 26):
    nc('U3', n)
# status LEDs
for k, (pin, unit, led, row, col, net, anet) in enumerate([
        (12, 1, 'D4', 40, 32, 'LED_GREEN', 'LED_G_A'),
        (13, 2, 'D5', 44, 33, 'LED_YELLOW', 'LED_Y_A'),
        (14, 3, 'D6', 48, 34, 'LED_RED', 'LED_R_A')]):
    sym('RN1', 40, row, rot=270, unit=unit)
    sym(led, 47.5, row, rot=180, rp=(47.5, row - 1.3), vp=(47.5, row + 1.35))
    p = P('U3', pin)
    W(p, (col, p[1]), (col, row), P('RN1', unit))
    lab(net, col + 0.5, row)
    W(P('RN1', 9 - unit), P(led, 2)); lab(anet, 41.5, row)
    W(P(led, 1), (51, row))
W((51, 40), (51, 50)); pwr(GND, 51, 50)
# ISP signals (labels to J2)
stub('U3', 15, 'MOSI'); stub('U3', 16, 'MISO'); stub('U3', 17, 'SCK')
# crystal
sym('Y1', 46, 57.5, rot=270, rp=(47.3, 57), vp=(47.3, 58.1), just='left', fa=90)
sym('C6', 52, 57.5); sym('C7', 46, 60.5)
W(P('U3', 7), P('C6', 1)); lab('XTAL1', 31, 56)
W(P('U3', 8), (42, 57), (42, 59), P('Y1', 2)); lab('XTAL2', 31, 57)
P('Y1', 1); P('C7', 1)
pwr(GND, *P('C6', 2)); pwr(GND, *P('C7', 2))
# analog / bus labels
stub('U3', 23, 'PRESS_ADC'); stub('U3', 27, 'SDA'); stub('U3', 28, 'SCL')
# reset
sym('RN2', 56, 62.5, unit=4)
sym('SW1', 64, 65, rp=(64, 62.5), vp=(64, 63.5))
W(P('U3', 29), P('SW1', 1)); lab('RESET', 31, 65)
W(P('RN2', 4), (56, 65)); pwr(V33, *P('RN2', 5))
W(P('SW1', 2), (67, 65), (67, 66)); pwr(GND, 67, 66)
# uart test points
sym('TP8', 38, 67, rp=(39.6, 66.4), vp=(39, 66), hide_val=True)
sym('TP9', 42, 68, rp=(43.6, 67.4), vp=(43, 67), hide_val=True)
W(P('U3', 30), P('TP8', 1)); lab('UART_RX', 31, 67)
W(P('U3', 31), P('TP9', 1)); lab('UART_TX', 31, 68)
# labels to other blocks
stub('U3', 32, 'ADXL_INT1'); stub('U3', 1, 'FAN_PWM'); stub('U3', 2, 'ONEWIRE_DQ')
stub('U3', 9, 'BUZZER_CTRL'); stub('U3', 10, 'RELAY_CTRL')
# ACK button
sym('SW2', 46, 74, rp=(46, 71.5), vp=(46, 72.5))
W(P('U3', 11), P('SW2', 1)); lab('BTN_ACK', 31, 74)
W(P('SW2', 2), (49, 74), (49, 75)); pwr(GND, 49, 75)
# ISP header
sym('J2', 56, 74, rp=(57.5, 69.6), vp=(57.5, 79), just='left')
stub('J2', 1, 'MISO'); stub('J2', 4, 'MOSI'); stub('J2', 3, 'SCK'); stub('J2', 5, 'RESET')
W(P('J2', 2), (55, 68)); pwr(V33, 55, 68)
W(P('J2', 6), (55, 79)); pwr(GND, 55, 79)
text('D4 = NORMAL, D5 = WARNING, D6 = CRITICAL', 32, 37.6)
text('ISP programmer must use 3.3V target', 44, 81.4)
text('TP8/TP9: debug UART', 37, 69.6)

# =====================================================================
# 3. VIBRATION SENSOR (I2C bus)
# =====================================================================
frame('3. VIBRATION SENSOR  ADXL345, I2C addr 0x53', 72, 26, 126, 52)
sym('U4', 100, 42, rp=(104, 45.2), vp=(104, 46.4), just='left')
W((74, 42), P('U4', 13)); lab('SDA', 74, 42)
W((74, 43), P('U4', 14)); lab('SCL', 74, 43)
sym('RN2', 79, 38.5, unit=1); sym('RN2', 86, 38.5, unit=2)
W(P('RN2', 1), (79, 42)); W(P('RN2', 2), (86, 43))
W(P('RN2', 8), (79, 36), (86, 36), P('RN2', 7))
W((82, 36), (82, 35)); pwr(V33, 82, 35)
sym('TP5', 89, 42, rp=(90.3, 40.9), vp=(89, 40), hide_val=True)
sym('TP6', 89, 43, rot=180, rp=(90.3, 44.4), vp=(89, 45), hide_val=True, fa=0)
P('TP5', 1); P('TP6', 1)
W(P('U4', 12), (93.5, 41)); pwr(GND, 93.5, 41, rot=270)
W(P('U4', 7), (91, 44), (91, 35), (112.5, 35))
lab('+3V3A', 91.5, 35)
flag(96, 35)
W(P('U4', 3), (98, 35)); W(P('U4', 6), (100, 35)); W(P('U4', 1), (102, 35))
sym('C8', 105, 36.5, rp=(105.8, 36.3), vp=(105.8, 37.4), just='left')
P('C8', 1); pwr(GND, *P('C8', 2))
sym('FB1', 114, 35, rot=270, rp=(114, 33.8), vp=(114, 36.3))
P('FB1', 2)
W(P('FB1', 1), (120, 35), (120, 34)); pwr(V33, 120, 34)
W(P('U4', 2), (100, 48)); pwr(GND, 100, 48)
W(P('U4', 11), (102, 48), (100, 48))
W(P('U4', 8), (107, 42)); lab('ADXL_INT1', 107, 42)
nc('U4', 9)
text('CS tied to VDDIO = I2C mode; SDO to GND = address 0x53; INT1 -> MCU PD2 (INT0)', 73, 51.4)
text('RN2A / RN2B: I2C pull-ups to 3.3V', 73, 50.2)

# =====================================================================
# 6. DISPLAY
# =====================================================================
frame('6. DISPLAY  OLED SSD1306 (optional)', 128, 26, 160, 52)
sym('J5', 146, 42, rp=(146, 38.9), vp=(146, 46.6))
W(P('J5', 1), (142, 41)); pwr(GND, 142, 41, rot=270)
W(P('J5', 2), (140, 42), (140, 40)); pwr(V33, 140, 40)
W(P('J5', 3), (138, 43)); lab('SCL', 138, 43, 'l')
W(P('J5', 4), (138, 44)); lab('SDA', 138, 44, 'l')
text('1 GND  2 VCC  3 SCL  4 SDA', 129, 51.4)

# =====================================================================
# 5. PRESSURE INPUT
# =====================================================================
frame('5. PRESSURE INPUT  0-5V sensor -> ADC0', 72, 54, 126, 80)
sym('J4', 78, 66, mirror='y', rp=(77.5, 63.3), vp=(78, 71.6))
W(P('J4', 1), (82, 65), (82, 63)); pwr(V5, 82, 63)
W(P('J4', 3), (82, 67), (82, 69)); pwr(GND, 82, 69)
sym('R1', 88, 66, rot=90)
W(P('J4', 2), P('R1', 1)); lab('PRESS_IN', 82.5, 66)
sym('R2', 94, 67.5); sym('C9', 100, 67.5)
sym('D3', 107, 64, rp=(106, 61.3), vp=(106, 62.4))
sym('TP7', 114, 66, rp=(114, 63.9), vp=(114, 63), hide_val=True)
W(P('R1', 2), (116, 66)); lab('PRESS_ADC', 116, 66)
P('R2', 1); P('C9', 1); P('D3', 3); P('TP7', 1)
pwr(GND, *P('R2', 2)); pwr(GND, *P('C9', 2))
W(P('D3', 1), (103, 64)); pwr(GND, 103, 64, rot=270)
W(P('D3', 2), (111, 64), (111, 63)); pwr(V33, 111, 63)
text('Divider R1/R2: Vadc = Vin x 0.643 (5.0V -> 3.21V); C9: low-pass ~250Hz', 73, 78.2)
text('D3 clamps the ADC pin to GND...3.3V; R1 limits fault current', 73, 79.4)

# =====================================================================
# 4. TEMPERATURE SENSOR
# =====================================================================
frame('4. TEMPERATURE  DS18B20 (external)', 128, 54, 160, 80)
sym('J3', 134, 66, mirror='y', rp=(133.5, 63.3), vp=(134, 71.6))
W(P('J3', 1), (138, 65), (138, 60)); pwr(V33, 138, 60)
sym('RN2', 144, 63.5, unit=3)
W((138, 62), P('RN2', 6))
W(P('RN2', 3), (144, 66))
W(P('J3', 2), (151, 66)); lab('ONEWIRE_DQ', 151, 66)
sym('D8', 148, 67.5, rot=90)
P('D8', 2); pwr(GND, *P('D8', 1))
W(P('J3', 3), (138, 67), (138, 69)); pwr(GND, 138, 69)
text('1 VDD  2 DQ  3 GND; RN2C: 1-Wire pull-up', 129, 78.2)
text('D8: ESD protection of the data line', 129, 79.4)

# =====================================================================
# 8-10. DRIVER, ALARM, RELAY, FAN
# =====================================================================
frame('8-10. ALARM, RELAY, FAN (ULN2003A)', 38, 84, 104, 112)
sym('U5', 56, 101, rp=(52.5, 94.4), vp=(52.5, 95.5), just='left')
W((40, 99), P('U5', 1)); lab('RELAY_CTRL', 40, 99)
W((40, 100), P('U5', 2)); lab('BUZZER_CTRL', 40, 100)
W(P('U5', 3), (50, 101)); W(P('U5', 5), (50, 103)); W((50, 101), (50, 103))
W((40, 102), (50, 102)); W((50, 102), P('U5', 4)); lab('FAN_PWM', 40, 102)
W(P('U5', 6), (51, 104)); W(P('U5', 7), (51, 105)); W((51, 104), (51, 106)); pwr(GND, 51, 106)
W(P('U5', 8), (56, 108)); pwr(GND, 56, 108)
nc('U5', 11); nc('U5', 10)
# relay state LED
sym('RN1', 50, 91, rot=270, unit=4, rp=(50, 89.8), vp=(50, 92.3))
sym('D7', 58, 91, rot=180, rp=(58, 89.7), vp=(55, 88.6))
W((47, 99), (47, 91), P('RN1', 4))
W(P('RN1', 5), P('D7', 2)); lab('LED_RLY_A', 51.5, 91)
W(P('D7', 1), (61, 91), (61, 92)); pwr(GND, 61, 92)
# +12V rail, relay
sym('K1', 78, 91, rp=(79.4, 96.5), vp=(79.4, 95.3), just='right')
W(P('U5', 9), (62, 97), (62, 87), (76, 87), P('K1', 5))
W((69, 87), (69, 86)); pwr(V12, 69, 86)
W(P('U5', 16), (64.5, 99), (64.5, 94), P('K1', 2)); lab('RELAY_N', 60.5, 99)
sym('J6', 96, 89, mirror='x', rp=(96.5, 86.1), vp=(96.5, 92.4))
W(P('K1', 4), (79, 87), (91, 87), (91, 88), P('J6', 3)); lab('RLY_NC', 84, 87)
W(P('K1', 3), (83, 88), (83, 90), P('J6', 1)); lab('RLY_NO', 84, 90)
W(P('K1', 1), (80, 96), (88, 96), (88, 89), P('J6', 2)); lab('RLY_COM', 81, 96)
# buzzer
sym('BZ1', 72, 100, rp=(76, 99.6), vp=(76, 100.8), just='left')
W(P('U5', 15), (68, 100), (68, 101), P('BZ1', 2)); lab('BUZZ_N', 60.5, 100)
W(P('BZ1', 1), (69, 99), (69, 98)); pwr(V5, 69, 98)
# fan
sym('J7', 96, 101, rp=(96.5, 99.1), vp=(96.5, 104))
W(P('U5', 14), (63, 101)); W(P('U5', 13), (63, 102)); W(P('U5', 12), (63, 103))
W((63, 101), (63, 104), (90, 104), (90, 102), P('J7', 2)); lab('FAN_N', 64, 104)
W(P('J7', 1), (92, 101), (92, 99)); pwr(V12, 92, 99)
text('Relay energised = NORMAL (fail-safe): load is fed through COM-NO; relay drops on alarm or power loss', 39, 110.2)
text('U5 COM -> +12V: built-in flyback diodes; fan uses 3 channels in parallel, max 0.6A, PWM from PD3', 39, 111.4)

# =====================================================================
# junctions (automatic)
# =====================================================================


def on_interior(p, w):
    (a, b) = w
    if abs(a[0] - b[0]) < 1e-6:
        return abs(p[0] - a[0]) < 1e-6 and min(a[1], b[1]) + 1e-6 < p[1] < max(a[1], b[1]) - 1e-6
    return abs(p[1] - a[1]) < 1e-6 and min(a[0], b[0]) + 1e-6 < p[0] < max(a[0], b[0]) - 1e-6


pts = {}
for a, b in wires:
    for p in (a, b):
        k = (round(p[0], 3), round(p[1], 3))
        pts[k] = pts.get(k, 0) + 1
pinset = {}
for p in pin_pts:
    k = (round(p[0], 3), round(p[1], 3))
    pinset[k] = pinset.get(k, 0) + 1
jn = 0
for k in set(pts) | set(pinset):
    ends = pts.get(k, 0)
    pn = pinset.get(k, 0)
    inter = any(on_interior(k, w) for w in wires)
    if (inter and (ends or pn)) or ends >= 3 or (ends >= 2 and pn >= 1) or (ends + pn >= 3):
        items.append('(junction (at %g %g) (diameter 0) (color 0 0 0 0) (uuid "%s"))' % (r(k[0] * U), r(k[1] * U), uid()))
        jn += 1
for a, b in wires:
    items.append('(wire (pts (xy %g %g) (xy %g %g)) (stroke (width 0) (type default)) (uuid "%s"))' % (
        r(a[0] * U), r(a[1] * U), r(b[0] * U), r(b[1] * U), uid()))

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
		(rev "2.1")
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
print('wires', len(wires), 'junctions', jn)
