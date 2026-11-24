import sys, time, json
import numpy as np
import pcbnew
import place
import route
from route import Router, own, RES, cell
from pcb_common import mm, MM

route.EDGE = 0.6
t0 = time.time()
R = Router('build/net.net')
b = R.b
ds = b.GetDesignSettings()
ds.m_MinClearance = mm(0.2)
ds.m_TrackMinWidth = mm(0.2)
ds.m_ViasMinSize = mm(0.6)
ds.m_MinThroughDrill = mm(0.3)
ds.m_CopperEdgeClearance = mm(0.3)

names = [n for n in R.pads if len(R.pads[n]) >= 2 and n != 'GND']


def hpwl(n):
    xs = [p['x'] for p in R.pads[n]]; ys = [p['y'] for p in R.pads[n]]
    return (max(xs) - min(xs)) + (max(ys) - min(ys))


load = ['/RLY_NC', '/RLY_COM', '/RLY_NO']
first = ['/VIN_RAW', '/VIN_FUSED', '/XTAL1', '/XTAL2', '+3V3A']
last = ['+12V', '/FAN_N', '+5V', '+3V3']
ORDER = sys.argv[1] if len(sys.argv) > 1 else 'a'
mid = sorted([n for n in names if n not in load + first + last], key=hpwl)
if ORDER == 'b':
    seq = load + first + last + mid
elif ORDER == 'c':
    seq = load + first + ['+12V', '/FAN_N'] + mid + ['+5V', '+3V3']
else:
    seq = load + first + mid + last

import os
prio = json.load(open('prio.json')) if os.path.exists('prio.json') else []
seq = [n for n in prio if n in seq] + [n for n in seq if n not in prio]
R.escapes(['U3', 'U4', 'U5', 'RN1', 'RN2', 'U2', 'D3'], float(sys.argv[2]) if len(sys.argv) > 2 else 1.2)
for n in load:
    R.route_net(n)
# isolation area around relay contacts / load terminal
KEEP = [(55.6, 16.4, 89.4, 21.6), (68.3, 10.2, 89.4, 27.9)]
for k in KEEP:
    R.block_rect(*k)
nv = R.gnd_vias()
for n in seq:
    if n in load:
        continue
    ok = R.route_net(n)
    if not ok:
        print('%-16s FAIL  %.0fs' % (n, time.time() - t0), flush=True)

ns = R.stitch()
print('gnd vias', nv, 'stitch', ns, 'total vias', R.nvias)
print('FAILED:', R.failed)
json.dump(R.failed, open('fail.json', 'w'))

# ---------------- zones ----------------
gnd = R.nets['GND']


def rect_zone(layer, x0, y0, x1, y1, rule=False):
    z = pcbnew.ZONE(b)
    ol = z.Outline()
    ol.NewOutline()
    for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
        ol.Append(mm(place.OX + x), mm(place.OY + y))
    if rule:
        z.SetIsRuleArea(True)
        z.SetDoNotAllowZoneFills(True)
        z.SetDoNotAllowTracks(False)
        z.SetDoNotAllowVias(False)
        z.SetDoNotAllowPads(False)
        z.SetDoNotAllowFootprints(False)
        ls = pcbnew.LSET()
        ls.AddLayer(pcbnew.F_Cu); ls.AddLayer(pcbnew.B_Cu)
        z.SetLayerSet(ls)
        z.SetZoneName('LOAD_ISOLATION')
    else:
        z.SetLayer(layer)
        z.SetNet(gnd)
        z.SetLocalClearance(mm(0.3))
        z.SetMinThickness(mm(0.25))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
        z.SetThermalReliefGap(mm(0.3))
        z.SetThermalReliefSpokeWidth(mm(0.4))
        z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
        z.SetZoneName('GND_' + ('F' if layer == pcbnew.F_Cu else 'B'))
    b.Add(z)
    return z


for k in KEEP:
    rect_zone(None, *k, rule=True)
zf = rect_zone(pcbnew.F_Cu, 0, 0, place.W, place.H)
zb = rect_zone(pcbnew.B_Cu, 0, 0, place.W, place.H)

# ---------------- silkscreen ----------------


def text(s, x, y, size=0.8, layer=pcbnew.F_SilkS, just=0, rot=0):
    t = pcbnew.PCB_TEXT(b)
    t.SetText(s)
    t.SetPosition(pcbnew.VECTOR2I(mm(place.OX + x), mm(place.OY + y)))
    t.SetTextSize(pcbnew.VECTOR2I(mm(size), mm(size)))
    t.SetTextThickness(mm(max(0.12, size * 0.15)))
    t.SetLayer(layer)
    if just == -1:
        t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_LEFT)
    if just == 1:
        t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_RIGHT)
    if rot:
        t.SetTextAngleDegrees(rot)
    b.Add(t)


SILK = json.load(open('silk.json'))
for s in SILK:
    text(*s)

# reference designators: uniform size
for fp in b.GetFootprints():
    r_ = fp.Reference()
    r_.SetTextSize(pcbnew.VECTOR2I(mm(0.8), mm(0.8)))
    r_.SetTextThickness(mm(0.13))
    if fp.GetReference().startswith('H'):
        r_.SetVisible(False)
    rp = {'J6': (84.1, 9.8), 'F1': (10.5, 17.9), 'TP2': (24.6, 18.0)}.get(fp.GetReference())
    if rp:
        r_.SetPosition(pcbnew.VECTOR2I(mm(place.OX + rp[0]), mm(place.OY + rp[1])))
        r_.SetTextAngleDegrees(0)

filler = pcbnew.ZONE_FILLER(b)
filler.Fill(b.Zones())
b.Save('build/Industry_PCB.kicad_pcb')
print('saved, tracks', len(b.GetTracks()), 'time %.0fs' % (time.time() - t0))
