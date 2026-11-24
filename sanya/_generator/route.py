"""Grid maze router (A*) for the 2-layer board, driven through the pcbnew API."""
import sys, math, heapq, time, json
import numpy as np
import pcbnew
import place
from pcb_common import make_board, add_outline, mm, MM

RES = 0.1
NX = int(round(place.W / RES)) + 1
NY = int(round(place.H / RES)) + 1
NN = NX * NY
CL = 0.2          # copper clearance
WSTD = 0.25
VIA_D, VIA_DRILL = 0.8, 0.4
MARGIN = 0.03
EDGE = 0.5
LAYERS = [pcbnew.F_Cu, pcbnew.B_Cu]

own = np.zeros((2, NY, NX), dtype=np.int16)
padmask = np.zeros((2, NY, NX), dtype=bool)
novia = np.zeros((NY, NX), dtype=bool)


def cell(v):
    return int(round(v / RES))


def stamp_rect(L, x0, y0, x1, y1, net, arr=None):
    ix0 = max(0, int(math.ceil(x0 / RES - 1e-9))); ix1 = min(NX - 1, int(math.floor(x1 / RES + 1e-9)))
    iy0 = max(0, int(math.ceil(y0 / RES - 1e-9))); iy1 = min(NY - 1, int(math.floor(y1 / RES + 1e-9)))
    if ix1 < ix0 or iy1 < iy0:
        return
    if arr is not None:
        arr[iy0:iy1 + 1, ix0:ix1 + 1] = True
        return
    reg = own[L, iy0:iy1 + 1, ix0:ix1 + 1]
    if net == -1:
        reg[:] = -1
    else:
        reg[(reg != 0) & (reg != net)] = -1
        reg[reg == 0] = net


_disc = {}


def disc(rad):
    k = int(math.floor(rad / RES + 1e-9))
    key = round(rad, 3)
    if key not in _disc:
        yy, xx = np.mgrid[-k:k + 1, -k:k + 1]
        _disc[key] = (k, (xx * xx + yy * yy) * RES * RES < rad * rad - 1e-9)
    return _disc[key]


def stamp_disc(L, iy, ix, rad, net, arr=None):
    k, m = disc(rad)
    y0, y1, x0, x1 = iy - k, iy + k + 1, ix - k, ix + k + 1
    my0, mx0 = max(0, -y0), max(0, -x0)
    y0, x0 = max(0, y0), max(0, x0)
    y1, x1 = min(NY, y1), min(NX, x1)
    mm_ = m[my0:my0 + (y1 - y0), mx0:mx0 + (x1 - x0)]
    if arr is not None:
        arr[y0:y1, x0:x1] |= mm_
        return
    reg = own[L, y0:y1, x0:x1]
    reg[mm_ & (reg != 0) & (reg != net)] = -1
    reg[mm_ & (reg == 0)] = net


def dilate(a, k):
    if k <= 0:
        return a
    out = a.copy()
    for s in range(1, k + 1):
        out[:, s:] |= a[:, :-s]
        out[:, :-s] |= a[:, s:]
    b = out.copy()
    for s in range(1, k + 1):
        out[s:, :] |= b[:-s, :]
        out[:-s, :] |= b[s:, :]
    return out


class Router:
    def __init__(self, netlist):
        self.b, self.fps, self.nets, self.comps, self.padnet = make_board(netlist, place)
        add_outline(self.b, place)
        self.netid = {}
        self.netname = {}
        self.pads = {}       # netname -> list of dict
        self.tracks = []
        self.failed = []
        self.keep_rects = []
        self.nvias = 0
        for name in self.nets:
            i = len(self.netid) + 1
            self.netid[name] = i
            self.netname[i] = name
        # board edge
        e = int(round(EDGE / RES))
        for L in (0, 1):
            own[L, :e, :] = -1; own[L, -e:, :] = -1; own[L, :, :e] = -1; own[L, :, -e:] = -1
        infl = CL + WSTD / 2 + MARGIN
        for ref, fp in self.fps.items():
            for pad in fp.Pads():
                bb = pad.GetBoundingBox()
                x0 = bb.GetLeft() / MM - place.OX; x1 = bb.GetRight() / MM - place.OX
                y0 = bb.GetTop() / MM - place.OY; y1 = bb.GetBottom() / MM - place.OY
                nname = pad.GetNetname()
                nid = self.netid.get(nname, -1)
                onF, onB = pad.IsOnLayer(pcbnew.F_Cu), pad.IsOnLayer(pcbnew.B_Cu)
                npth = pad.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH
                if npth:
                    for L in (0, 1):
                        stamp_rect(L, x0 - infl - 0.15, y0 - infl - 0.15, x1 + infl + 0.15, y1 + infl + 0.15, -1)
                    stamp_rect(0, x0 - 0.8, y0 - 0.8, x1 + 0.8, y1 + 0.8, 0, arr=novia)
                    continue
                if not (onF or onB):
                    continue
                for L, on in ((0, onF), (1, onB)):
                    if on:
                        stamp_rect(L, x0 - infl, y0 - infl, x1 + infl, y1 + infl, nid)
                        stamp_rect(L, x0, y0, x1, y1, 0, arr=padmask[L])
                stamp_rect(0, x0 - 0.45, y0 - 0.45, x1 + 0.45, y1 + 0.45, 0, arr=novia)
                if nid > 0:
                    c = pad.GetPosition()
                    self.pads.setdefault(nname, []).append(dict(
                        ref=ref, num=pad.GetNumber(), x=c.x / MM - place.OX, y=c.y / MM - place.OY,
                        layers=[L for L, on in ((0, onF), (1, onB)) if on], bb=(x0, y0, x1, y1)))

    # ---------------------------------------------------------------
    def passmaps(self, nid, width):
        k = int(math.ceil((width - WSTD) / 2 / RES - 1e-9)) if width > WSTD else 0
        blocked = (own != 0) & (own != nid)
        pt = [~dilate(blocked[L], k) for L in (0, 1)]
        kv = int(math.ceil((VIA_D - WSTD) / 2 / RES - 1e-9))
        pv = ~dilate(blocked[0] | blocked[1], max(kv, k)) & ~padmask[0] & ~padmask[1] & ~novia
        return pt, pv

    def pad_cells(self, p, pt):
        """passable cells near the pad centre, for each pad layer"""
        res = []
        cx, cy = cell(p['x']), cell(p['y'])
        for L in p['layers']:
            best = None
            for r in range(0, 6):
                for dy in range(-r, r + 1):
                    for dx in range(-r, r + 1):
                        if max(abs(dx), abs(dy)) != r:
                            continue
                        x, y = cx + dx, cy + dy
                        if not (0 <= x < NX and 0 <= y < NY):
                            continue
                        # stay inside pad copper
                        if not (p['bb'][0] <= x * RES <= p['bb'][2] and p['bb'][1] <= y * RES <= p['bb'][3]):
                            continue
                        if pt[L][y, x]:
                            d = (x * RES - p['x']) ** 2 + (y * RES - p['y']) ** 2
                            if best is None or d < best[0]:
                                best = (d, L, y, x)
                if best:
                    break
            if best:
                res.append(best[1:])
        return res

    def astar(self, pt, pv, sources, tgt, thru, hpts, bcost=1.6, viacost=250):
        ptb = [pt[0].tobytes(), pt[1].tobytes()]
        pvb = pv.tobytes()
        tgb = [tgt[0].tobytes(), tgt[1].tobytes()]
        g = {}
        par = {}
        heap = []

        def h(iy, ix):
            m = 10 ** 9
            for (ty, tx) in hpts:
                dx, dy = abs(tx - ix), abs(ty - iy)
                d = 10 * max(dx, dy) + 4 * min(dx, dy)
                if d < m:
                    m = d
            return m
        for (L, iy, ix) in sources:
            idx = L * NN + iy * NX + ix
            g[idx] = 0
            par[idx] = -1
            heapq.heappush(heap, (h(iy, ix), 0, idx))
        moves = ((1, 0, 10), (-1, 0, 10), (0, 1, 10), (0, -1, 10), (1, 1, 14), (1, -1, 14), (-1, 1, 14), (-1, -1, 14))
        n = 0
        while heap:
            f, gc, idx = heapq.heappop(heap)
            if g.get(idx, 1 << 60) < gc:
                continue
            L, rem = divmod(idx, NN)
            iy, ix = divmod(rem, NX)
            if tgb[L][rem]:
                path = []
                while idx != -1:
                    l, r_ = divmod(idx, NN)
                    y, x = divmod(r_, NX)
                    path.append((l, y, x))
                    idx = par[idx]
                return path[::-1]
            n += 1
            if n > 1500000:
                return None
            p = ptb[L]
            mul = bcost if L == 1 else 1.0
            for dx, dy, c in moves:
                x, y = ix + dx, iy + dy
                if x < 0 or y < 0 or x >= NX or y >= NY:
                    continue
                r2 = y * NX + x
                if not p[r2]:
                    continue
                if dx and dy and not (p[iy * NX + x] and p[y * NX + ix]):
                    continue
                ng = gc + int(c * mul)
                i2 = L * NN + r2
                if ng < g.get(i2, 1 << 60):
                    g[i2] = ng
                    par[i2] = idx
                    heapq.heappush(heap, (ng + h(y, x), ng, i2))
            # layer change
            o = 1 - L
            if ptb[o][rem]:
                vc = None
                if (iy, ix) in thru:
                    vc = 0
                elif pvb[rem]:
                    vc = viacost
                if vc is not None:
                    ng = gc + vc
                    i2 = o * NN + rem
                    if ng < g.get(i2, 1 << 60):
                        g[i2] = ng
                        par[i2] = idx
                        heapq.heappush(heap, (ng + h(iy, ix), ng, i2))
        return None

    # ---------------------------------------------------------------
    def add_track(self, x0, y0, x1, y1, L, width, nname):
        if abs(x0 - x1) < 1e-6 and abs(y0 - y1) < 1e-6:
            return
        t = pcbnew.PCB_TRACK(self.b)
        t.SetStart(pcbnew.VECTOR2I(mm(place.OX + x0), mm(place.OY + y0)))
        t.SetEnd(pcbnew.VECTOR2I(mm(place.OX + x1), mm(place.OY + y1)))
        t.SetWidth(mm(width))
        t.SetLayer(LAYERS[L])
        t.SetNet(self.nets[nname])
        self.b.Add(t)

    def add_via(self, x, y, nname):
        v = pcbnew.PCB_VIA(self.b)
        v.SetPosition(pcbnew.VECTOR2I(mm(place.OX + x), mm(place.OY + y)))
        v.SetWidth(mm(VIA_D))
        v.SetDrill(mm(VIA_DRILL))
        v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        v.SetNet(self.nets[nname])
        self.b.Add(v)
        self.nvias += 1
        iy, ix = cell(y), cell(x)
        nid = self.netid[nname]
        for L in (0, 1):
            stamp_disc(L, iy, ix, VIA_D / 2 + CL + WSTD / 2 + MARGIN, nid)
        stamp_disc(0, iy, ix, 1.0, 0, arr=novia)

    def emit(self, path, width, nname, thru, exact):
        nid = self.netid[nname]
        rad = width / 2 + CL + WSTD / 2 + MARGIN
        pts = []   # (L, x, y)
        for (L, iy, ix) in path:
            pts.append((L, ix * RES, iy * RES))
            stamp_disc(L, iy, ix, rad, nid)
        # exact pad centre attach
        for end in (0, -1):
            L, iy, ix = path[end]
            if (L, iy, ix) in exact:
                ex, ey = exact[(L, iy, ix)]
                self.add_track(ex, ey, ix * RES, iy * RES, L, min(width, 0.6) if width > 0.6 else width, nname)
        i = 0
        while i < len(pts) - 1:
            L, x, y = pts[i]
            L2, x2, y2 = pts[i + 1]
            if L2 != L:
                if (cell(y), cell(x)) not in thru:
                    self.add_via(x, y, nname)
                i += 1
                continue
            d = (round(x2 - x, 3), round(y2 - y, 3))
            j = i + 1
            while j < len(pts) - 1 and pts[j + 1][0] == L and (round(pts[j + 1][1] - pts[j][1], 3), round(pts[j + 1][2] - pts[j][2], 3)) == d:
                j += 1
            self.add_track(x, y, pts[j][1], pts[j][2], L, width, nname)
            i = j

    def route_net(self, nname, order_seed=0):
        pads = self.pads.get(nname, [])
        if len(pads) < 2:
            return True
        nid = self.netid[nname]
        width = place.WIDTH.get(nname, WSTD)
        pt, pv = self.passmaps(nid, width)
        tgt = np.zeros((2, NY, NX), dtype=bool)
        thru = set()
        exact = {}
        pcs = []
        for p in pads:
            cs = self.pad_cells(p, pt)
            pcs.append(cs)
            for (L, y, x) in cs:
                exact[(L, y, x)] = (p['x'], p['y'])
            if len(p['layers']) == 2 and len(cs) == 2 and cs[0][1:] == cs[1][1:]:
                thru.add(cs[0][1:])
        # start tree: pad closest to centroid
        cx = sum(p['x'] for p in pads) / len(pads); cy = sum(p['y'] for p in pads) / len(pads)
        rest = list(range(len(pads)))
        first = min(rest, key=lambda i: (pads[i]['x'] - cx) ** 2 + (pads[i]['y'] - cy) ** 2)
        tree = [first]
        rest.remove(first)
        for (L, y, x) in pcs[first]:
            tgt[L, y, x] = True
        ok = True
        while rest:
            nxt = min(rest, key=lambda i: min((pads[i]['x'] - pads[j]['x']) ** 2 + (pads[i]['y'] - pads[j]['y']) ** 2 for j in tree))
            rest.remove(nxt)
            if not pcs[nxt]:
                self.failed.append((nname, pads[nxt]['ref'], pads[nxt]['num'], 'no pad access'))
                ok = False
                continue
            hpts = [(cell(pads[j]['y']), cell(pads[j]['x'])) for j in tree]
            path = self.astar(pt, pv, pcs[nxt], tgt, thru, hpts)
            if path is None:
                self.failed.append((nname, pads[nxt]['ref'], pads[nxt]['num'], 'no route'))
                ok = False
                continue
            self.emit(path, width, nname, thru, exact)
            for (L, y, x) in path:
                tgt[L, y, x] = True
            for (L, y, x) in pcs[nxt]:
                tgt[L, y, x] = True
            tree.append(nxt)
        return ok

    def block_rect(self, x0, y0, x1, y1):
        """make all still-free cells in rect unusable (both layers)"""
        self.keep_rects.append((x0, y0, x1, y1))
        ix0, ix1, iy0, iy1 = cell(x0), cell(x1), cell(y0), cell(y1)
        for L in (0, 1):
            reg = own[L, iy0:iy1 + 1, ix0:ix1 + 1]
            reg[reg == 0] = -1

    def gnd_vias(self, nname='GND'):
        nid = self.netid[nname]
        made = 0
        for p in self.pads.get(nname, []):
            if len(p['layers']) == 2:
                continue
            pt, pv = self.passmaps(nid, WSTD)
            cs = self.pad_cells(p, pt)
            if not cs:
                self.failed.append((nname, p['ref'], p['num'], 'gnd pad access'))
                continue
            L = p['layers'][0]
            tgt = np.zeros((2, NY, NX), dtype=bool)
            tgt[L] = pv & pt[1 - L]
            # do not allow layer change inside search
            path = self.astar(pt, np.zeros((NY, NX), dtype=bool), cs, tgt, set(), [(cs[0][1], cs[0][2])])
            if path is None or len(path) > 80:
                self.failed.append((nname, p['ref'], p['num'], 'gnd via'))
                continue
            exact = {c: (p['x'], p['y']) for c in cs}
            self.emit(path, WSTD if len(path) > 1 else WSTD, nname, set(), exact)
            if len(path) == 1:
                self.add_track(p['x'], p['y'], path[0][2] * RES, path[0][1] * RES, L, WSTD, nname)
            self.add_via(path[-1][2] * RES, path[-1][1] * RES, nname)
            made += 1
        return made

    def stitch(self, nname='GND', pitch=7.0):
        nid = self.netid[nname]
        n = 0
        y = 3.0
        while y < place.H - 2:
            x = 3.0
            while x < place.W - 2:
                pt, pv = None, None
                iy, ix = cell(y), cell(x)
                blocked = (own[:, iy - 8:iy + 9, ix - 8:ix + 9] != 0) & (own[:, iy - 8:iy + 9, ix - 8:ix + 9] != nid)
                if not blocked.any() and not padmask[:, iy - 5:iy + 6, ix - 5:ix + 6].any() and not novia[iy - 3:iy + 4, ix - 3:ix + 4].any():
                    self.add_via(x, y, nname)
                    n += 1
                x += pitch
            y += pitch
        return n


def _escapes(self, refs, length=1.2):
    """reserve a straight escape channel in front of every connected SMD pad of the given parts"""
    rad = WSTD + CL + MARGIN
    for ref in refs:
        fp = self.fps[ref]
        c = fp.GetPosition()
        fx, fy = c.x / MM - place.OX, c.y / MM - place.OY
        # use pad-centroid as body centre
        ps = [p for n in self.pads for p in self.pads[n] if p['ref'] == ref]
        if not ps:
            continue
        fx = sum(p['x'] for p in ps) / len(ps); fy = sum(p['y'] for p in ps) / len(ps)
        for n, lst in self.pads.items():
            if len(lst) < 2:
                continue
            nid = self.netid[n]
            for p in lst:
                if p['ref'] != ref or len(p['layers']) != 1:
                    continue
                w = p['bb'][2] - p['bb'][0]; h = p['bb'][3] - p['bb'][1]
                if w >= h:
                    d = (1 if p['x'] > fx else -1, 0)
                    start = w / 2
                else:
                    d = (0, 1 if p['y'] > fy else -1)
                    start = h / 2
                L = p['layers'][0]
                s = 0.0
                while s <= start + length:
                    stamp_disc(L, cell(p['y'] + d[1] * s), cell(p['x'] + d[0] * s), rad, nid)
                    s += RES


Router.escapes = _escapes
