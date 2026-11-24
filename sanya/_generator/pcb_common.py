import os, sys, json, importlib
import pcbnew
import sx

FPDIR = r"C:\Program Files\KiCad\10.0\share\kicad\footprints"
MM = 1000000


def mm(v):
    return int(round(v * MM))


def read_netlist(path):
    t = sx.parse(open(path, encoding='utf-8').read())
    comps = {}
    for c in sx.find(sx.first(t, 'components'), 'comp'):
        ref = str(sx.first(c, 'ref')[1])
        fields = {}
        f = sx.first(c, 'fields')
        if f:
            for fl in sx.find(f, 'field'):
                nm = str(sx.first(fl, 'name')[1])
                fields[nm] = str(fl[2]) if len(fl) > 2 else ''
        comps[ref] = dict(value=str(sx.first(c, 'value')[1]), fp=str(sx.first(c, 'footprint')[1]),
                          ts=str(sx.first(c, 'tstamps')[1]), fields=fields)
    padnet = {}
    for n in sx.find(sx.first(t, 'nets'), 'net'):
        name = str(sx.first(n, 'name')[1])
        for nd in sx.find(n, 'node'):
            pf = sx.first(nd, 'pinfunction')
            pt = sx.first(nd, 'pintype')
            padnet[(str(sx.first(nd, 'ref')[1]), str(sx.first(nd, 'pin')[1]))] = (name, str(pf[1]) if pf else '', str(pt[1]) if pt else '')
    return comps, padnet


def make_board(netlist, place):
    comps, padnet = read_netlist(netlist)
    b = pcbnew.BOARD()
    nets = {}

    def net(name):
        if name not in nets:
            ni = pcbnew.NETINFO_ITEM(b, name)
            b.Add(ni)
            nets[name] = ni
        return nets[name]

    fps = {}
    for ref, c in comps.items():
        lib, name = c['fp'].split(':')
        fp = pcbnew.FootprintLoad(os.path.join(FPDIR, lib + '.pretty'), name)
        assert fp, c['fp']
        fp.SetFPID(pcbnew.LIB_ID(lib, name))
        fp.SetReference(ref)
        fp.SetValue(c['value'])
        fp.SetPath(pcbnew.KIID_PATH('/' + c['ts']))
        fp.SetSheetname('/')
        fp.SetSheetfile('Industry_PCB.kicad_sch')
        for k, v in c['fields'].items():
            if k in ('MPN', 'Manufacturer') and v:
                fp.SetField(k, v)
        for f in fp.GetFields():
            if f.GetName() in ('MPN', 'Manufacturer'):
                f.SetVisible(False)
                f.SetLayer(pcbnew.F_Fab)
        b.Add(fp)
        cx, cy, rot = place.P[ref]
        fp.SetOrientationDegrees(rot)
        fp.SetPosition(pcbnew.VECTOR2I(mm(place.OX), mm(place.OY)))
        bb = courtyard_bbox(fp)
        dx = mm(place.OX + cx) - (bb[0] + bb[2]) // 2
        dy = mm(place.OY + cy) - (bb[1] + bb[3]) // 2
        # snap final position to 0.05 mm
        pos = fp.GetPosition()
        nx = int(round((pos.x + dx) / 50000.0)) * 50000
        ny = int(round((pos.y + dy) / 50000.0)) * 50000
        fp.SetPosition(pcbnew.VECTOR2I(nx, ny))
        for pad in fp.Pads():
            k = (ref, pad.GetNumber())
            if k in padnet:
                pad.SetNet(net(padnet[k][0]))
                pad.SetPinFunction(padnet[k][1])
                pad.SetPinType(padnet[k][2])
        fps[ref] = fp
    return b, fps, nets, comps, padnet


def courtyard_bbox(fp):
    x0 = y0 = 10 ** 12
    x1 = y1 = -10 ** 12
    found = False
    for g in fp.GraphicalItems():
        if g.GetLayer() in (pcbnew.F_CrtYd, pcbnew.B_CrtYd):
            bb = g.GetBoundingBox()
            x0 = min(x0, bb.GetLeft()); y0 = min(y0, bb.GetTop())
            x1 = max(x1, bb.GetRight()); y1 = max(y1, bb.GetBottom())
            found = True
    if not found:
        for pad in fp.Pads():
            bb = pad.GetBoundingBox()
            x0 = min(x0, bb.GetLeft()); y0 = min(y0, bb.GetTop())
            x1 = max(x1, bb.GetRight()); y1 = max(y1, bb.GetBottom())
    return (x0, y0, x1, y1)


def add_outline(b, place):
    r = pcbnew.PCB_SHAPE(b)
    r.SetShape(pcbnew.SHAPE_T_RECTANGLE)
    r.SetStart(pcbnew.VECTOR2I(mm(place.OX), mm(place.OY)))
    r.SetEnd(pcbnew.VECTOR2I(mm(place.OX + place.W), mm(place.OY + place.H)))
    r.SetLayer(pcbnew.Edge_Cuts)
    r.SetWidth(mm(0.1))
    b.Add(r)


if __name__ == '__main__':
    import place
    b, fps, nets, comps, padnet = make_board('build/net.net', place)
    add_outline(b, place)
    boxes = {}
    for ref, fp in fps.items():
        bb = courtyard_bbox(fp)
        boxes[ref] = [(v / MM) for v in bb]
        boxes[ref] = [boxes[ref][0] - place.OX, boxes[ref][1] - place.OY, boxes[ref][2] - place.OX, boxes[ref][3] - place.OY]
    refs = sorted(boxes)
    for r_ in refs:
        x0, y0, x1, y1 = boxes[r_]
        flag = ''
        if x0 < 0.3 or y0 < 0.3 or x1 > place.W - 0.3 or y1 > place.H - 0.3:
            flag = ' OUT'
        print('%-4s %6.2f %6.2f %6.2f %6.2f  %5.1fx%-5.1f%s' % (r_, x0, y0, x1, y1, x1 - x0, y1 - y0, flag))
    for i, a in enumerate(refs):
        for c in refs[i + 1:]:
            A, B = boxes[a], boxes[c]
            if A[0] < B[2] and B[0] < A[2] and A[1] < B[3] and B[1] < A[3]:
                print('OVERLAP', a, c)
    for ref in ('K1', 'J6', 'J1', 'J7', 'J5', 'J2', 'J3', 'J4', 'U3', 'SW1', 'BZ1'):
        print(ref, [(p.GetNumber(), round(p.GetPosition().x / MM - place.OX, 2), round(p.GetPosition().y / MM - place.OY, 2)) for p in fps[ref].Pads() if p.GetNumber() in ('1', '2', '3', '4', '5', '9', '17', '25')])
    b.Save('build/Industry_PCB.kicad_pcb')
