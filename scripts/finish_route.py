"""Finish what the autorouter left open: join split nets with A* tracks, and
give every cluster of a plane net (GND / VBUS / +5V_STRIP) a via into its plane."""
import sys, math, heapq
import pcbnew

PCB = sys.argv[1]
G = 0.1                       # grid, mm
X0, Y0, W, H = 100.0, 100.0, 66.0, 32.0
NX, NY = int(W / G) + 1, int(H / G) + 1
CLR = 0.15
EDGE = 0.55
VIA_D, VIA_DR = 0.6, 0.3
SLACK = 0.06

b = pcbnew.LoadBoard(PCB)
F, B = pcbnew.F_Cu, pcbnew.B_Cu
mm = pcbnew.ToMM


def inside_rect(x, y, r):
    return r[0] <= x <= r[2] and r[1] <= y <= r[3]


VBUS_R = [(101.4, 101.4, 125.6, 118.6)]
STRIP_R = [(127.6, 101.4, 146.3, 130.6), (108.7, 120.6, 146.3, 130.6)]
GND_R = [(100.8, 100.8, 160.6, 131.2)]
PLANES = {"VBUS": VBUS_R, "+5V_STRIP": STRIP_R, "GND": GND_R}
HEAVY = {("J1", "A4"), ("J1", "A9"), ("J1", "B4"), ("J1", "B9"), ("U1", "4"), ("U1", "5"),
         ("C3", "1"), ("J2", "1"), ("J3", "1"), ("U2", "1")}

FPS = list(b.GetFootprints())
TRACK_OBJS = list(b.GetTracks())
DEAD = []
keepouts = []
for fp in FPS:
    for z in fp.Zones():
        if z.GetIsRuleArea():
            bb = z.GetBoundingBox()
            keepouts.append((mm(bb.GetLeft()), mm(bb.GetTop()), mm(bb.GetRight()), mm(bb.GetBottom())))


PAD_ITEMS = None


def items():
    global PAD_ITEMS
    if PAD_ITEMS is None:
        PAD_ITEMS = _pad_items()
    return [dict(p) for p in PAD_ITEMS] + _track_items()


def _pad_items():
    out = []
    for fp in FPS:
        for p in fp.Pads():
            bb = p.GetBoundingBox()
            r = ("rect", mm(bb.GetLeft()), mm(bb.GetTop()), mm(bb.GetRight()), mm(bb.GetBottom()))
            ls = p.GetLayerSet()
            layers = set()
            pth = p.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH)
            if pth or ls.Contains(F):
                layers.add(F)
            if pth or ls.Contains(B):
                layers.add(B)
            if not layers:
                continue
            out.append({"net": p.GetNetname(), "kind": "pad", "layers": layers, "g": r, "pth": pth,
                        "ref": fp.GetReference(), "num": p.GetNumber(),
                        "c": (mm(p.GetPosition().x), mm(p.GetPosition().y))})
    return out


def _track_items():
    out = []
    for t in list(TRACK_OBJS):
        if t.Type() == pcbnew.PCB_VIA_T:
            x, y = mm(t.GetPosition().x), mm(t.GetPosition().y)
            out.append({"net": t.GetNetname(), "kind": "via", "layers": {F, B},
                        "g": ("cap", x, y, x, y, mm(t.GetWidth(F)) / 2), "pth": True, "c": (x, y)})
        else:
            s, e = t.GetStart(), t.GetEnd()
            out.append({"net": t.GetNetname(), "kind": "seg", "layers": {t.GetLayer()},
                        "g": ("cap", mm(s.x), mm(s.y), mm(e.x), mm(e.y), mm(t.GetWidth()) / 2), "pth": False,
                        "c": (mm(s.x), mm(s.y))})
    return out


def dist_pt_seg(px, py, x1, y1, x2, y2):
    dx, dy = x2 - x1, y2 - y1
    if dx == 0 and dy == 0:
        return math.hypot(px - x1, py - y1)
    t = max(0, min(1, ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - x1 - t * dx, py - y1 - t * dy)


def touch(a, c):
    if not (a["layers"] & c["layers"]):
        return False
    ga, gc = a["g"], c["g"]
    if ga[0] == "rect" and gc[0] == "rect":
        return not (ga[3] < gc[1] or gc[3] < ga[1] or ga[4] < gc[2] or gc[4] < ga[2])
    if ga[0] == "rect":
        ga, gc = gc, ga
    if gc[0] == "rect":          # capsule vs rect: any end inside (slightly grown) rect
        for (x, y) in ((ga[1], ga[2]), (ga[3], ga[4])):
            if gc[1] - 0.02 <= x <= gc[3] + 0.02 and gc[2] - 0.02 <= y <= gc[4] + 0.02:
                return True
        return False
    for (x, y) in ((ga[1], ga[2]), (ga[3], ga[4])):
        if dist_pt_seg(x, y, gc[1], gc[2], gc[3], gc[4]) <= max(gc[5], 0.02) + 0.01:
            return True
    for (x, y) in ((gc[1], gc[2]), (gc[3], gc[4])):
        if dist_pt_seg(x, y, ga[1], ga[2], ga[3], ga[4]) <= max(ga[5], 0.02) + 0.01:
            return True
    return False


def clusters(net, its):
    mine = [i for i in its if i["net"] == net]
    par = list(range(len(mine)))

    def find(i):
        while par[i] != i:
            par[i] = par[par[i]]
            i = par[i]
        return i
    for i in range(len(mine)):
        for j in range(i + 1, len(mine)):
            if touch(mine[i], mine[j]):
                par[find(i)] = find(j)
    groups = {}
    for i, it in enumerate(mine):
        groups.setdefault(find(i), []).append(it)
    return list(groups.values())


def cell(x, y):
    return int(round((x - X0) / G)), int(round((y - Y0) / G))


def blank():
    return bytearray(NX * NY)


def mark(grid, g, infl):
    if g[0] == "rect":
        x1, y1, x2, y2 = g[1] - infl, g[2] - infl, g[3] + infl, g[4] + infl
        cx1, cy1 = cell(x1, y1)
        cx2, cy2 = cell(x2, y2)
        for cy in range(max(0, cy1), min(NY - 1, cy2) + 1):
            for cx in range(max(0, cx1), min(NX - 1, cx2) + 1):
                grid[cy * NX + cx] = 1
    else:
        _, x1, y1, x2, y2, r = g
        r += infl
        cx1, cy1 = cell(min(x1, x2) - r, min(y1, y2) - r)
        cx2, cy2 = cell(max(x1, x2) + r, max(y1, y2) + r)
        for cy in range(max(0, cy1), min(NY - 1, cy2) + 1):
            py = Y0 + cy * G
            for cx in range(max(0, cx1), min(NX - 1, cx2) + 1):
                if dist_pt_seg(X0 + cx * G, py, x1, y1, x2, y2) <= r:
                    grid[cy * NX + cx] = 1


def obstacle_maps(net, its, half, hard_only=False):
    """Blocked cells for a track of half-width `half` on F and B, and for a via."""
    gf, gb, gv = blank(), blank(), blank()
    for grid, extra in ((gf, half), (gb, half), (gv, VIA_D / 2)):
        e = int(round((EDGE + extra - 0.05) / G))
        for cy in range(NY):
            for cx in range(NX):
                if cx < e or cy < e or cx > NX - 1 - e or cy > NY - 1 - e:
                    grid[cy * NX + cx] = 1
        for k in keepouts:
            mark(grid, ("rect",) + k, extra)
    for it in its:
        if it["net"] == net:
            continue
        if hard_only and it["kind"] != "pad":
            continue
        tight = it.get("ref") == "U4"
        infl = (0.1 + 0.03 if tight else CLR + SLACK) + half
        if F in it["layers"]:
            mark(gf, it["g"], infl)
        if B in it["layers"]:
            mark(gb, it["g"], infl)
        # a via lands on both outer layers; holes need 0.25 hole-to-hole too
        mark(gv, it["g"], CLR + VIA_D / 2 + SLACK + (0.1 if it["pth"] else 0))
    return {F: gf, B: gb}, gv


def seeds(cluster):
    out = []
    for it in cluster:
        g = it["g"]
        pts = [it["c"]] if g[0] == "rect" else [(g[1], g[2]), (g[3], g[4])]
        for (x, y) in pts:
            cx, cy = cell(x, y)
            if 0 <= cx < NX and 0 <= cy < NY:
                for l in it["layers"]:
                    out.append((l, cx, cy))
    return out


MOVES = [(1, 0, 10), (-1, 0, 10), (0, 1, 10), (0, -1, 10), (1, 1, 14), (1, -1, 14), (-1, 1, 14), (-1, -1, 14)]


def astar(src, goal_fn, grids, gv, allow_via=True, via_ok=None, max_nodes=900000, hard=None):
    """Dijkstra from src cells to the first cell where goal_fn(l,cx,cy) is true."""
    dist, prev, pq = {}, {}, []
    for s in src:
        dist[s] = 0
        heapq.heappush(pq, (0, s))
    n = 0
    while pq:
        d, cur = heapq.heappop(pq)
        if d > dist.get(cur, 1e18):
            continue
        n += 1
        if n > max_nodes:
            LAST[0] = n
            return None
        l, cx, cy = cur
        if goal_fn(l, cx, cy) and cur not in src_set:
            path = [cur]
            while cur in prev:
                cur = prev[cur]
                path.append(cur)
            return path[::-1]
        g = grids[l]
        for dx, dy, c in MOVES:
            nx, ny = cx + dx, cy + dy
            if not (0 <= nx < NX and 0 <= ny < NY):
                continue
            pen = 0
            if g[ny * NX + nx] and (l, nx, ny) not in free_set:
                if hard is None or hard[l][ny * NX + nx]:
                    continue
                pen = 400
            if dx and dy and ((g[cy * NX + nx] and (l, nx, cy) not in free_set)
                              or (g[ny * NX + cx] and (l, cx, ny) not in free_set)):
                continue
            nd = d + c + pen
            k = (l, nx, ny)
            if nd < dist.get(k, 1e18):
                dist[k] = nd
                prev[k] = cur
                heapq.heappush(pq, (nd, k))
        if allow_via and not gv[cy * NX + cx] and (via_ok is None or via_ok(cx, cy)):
            ol = B if l == F else F
            if not grids[ol][cy * NX + cx]:
                nd = d + 300
                k = (ol, cx, cy)
                if nd < dist.get(k, 1e18):
                    dist[k] = nd
                    prev[k] = cur
                    heapq.heappush(pq, (nd, k))
    LAST[0] = n
    return None


src_set, free_set = set(), set()
LAST = [0]


def emit(path, net, width):
    """Turn a cell path into tracks and vias on the board."""
    code = b.FindNet(net)
    run = [path[0]]

    def flush(run):
        if len(run) < 2:
            return
        # merge collinear steps
        pts = [run[0]]
        for i in range(1, len(run) - 1):
            a, c, n = run[i - 1], run[i], run[i + 1]
            if (c[1] - a[1], c[2] - a[2]) != (n[1] - c[1], n[2] - c[2]):
                pts.append(c)
        pts.append(run[-1])
        for a, c in zip(pts, pts[1:]):
            t = pcbnew.PCB_TRACK(b)
            t.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(X0 + a[1] * G), pcbnew.FromMM(Y0 + a[2] * G)))
            t.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(X0 + c[1] * G), pcbnew.FromMM(Y0 + c[2] * G)))
            t.SetWidth(pcbnew.FromMM(width))
            t.SetLayer(a[0])
            t.SetNet(code)
            b.Add(t)
            TRACK_OBJS.append(t)
    for p in path[1:]:
        if p[0] != run[-1][0]:
            flush(run)
            add_via(p[1], p[2], net)
            run = [p]
        else:
            run.append(p)
    flush(run)


def add_via(cx, cy, net):
    v = pcbnew.PCB_VIA(b)
    v.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(X0 + cx * G), pcbnew.FromMM(Y0 + cy * G)))
    v.SetWidth(pcbnew.F_Cu, pcbnew.FromMM(VIA_D)) if hasattr(v, "SetWidth") else None
    v.SetDrill(pcbnew.FromMM(VIA_DR))
    v.SetLayerPair(F, B)
    v.SetNet(b.FindNet(net))
    b.Add(v)
    TRACK_OBJS.append(v)


def pad_escape(cluster, grids):
    """Cells under the cluster's own copper are always enterable."""
    fs = set()
    for it in cluster:
        g = it["g"]
        if g[0] == "rect":
            x1, y1, x2, y2 = g[1], g[2], g[3], g[4]
            r = 0.0
        else:
            x1, y1, x2, y2 = min(g[1], g[3]), min(g[2], g[4]), max(g[1], g[3]), max(g[2], g[4])
            r = max(g[5] - 0.03, 0.05)
        cx1, cy1 = cell(x1 - r, y1 - r)
        cx2, cy2 = cell(x2 + r, y2 + r)
        for cy in range(max(0, cy1), min(NY - 1, cy2) + 1):
            for cx in range(max(0, cx1), min(NX - 1, cx2) + 1):
                px, py = X0 + cx * G, Y0 + cy * G
                if g[0] == "rect":
                    hit = g[1] <= px <= g[3] and g[2] <= py <= g[4]
                else:
                    hit = dist_pt_seg(px, py, g[1], g[2], g[3], g[4]) <= r
                if hit:
                    for l in it["layers"]:
                        fs.add((l, cx, cy))
    return fs


def in_plane(net, x, y):
    return any(inside_rect(x, y, r) for r in PLANES[net])


report = []
sig_nets = sorted({i["net"] for i in items() if i["net"] and not i["net"].startswith("unconnected")})

def rip_blockers(path, net, half):
    """Remove other nets' tracks and vias that sit too close to `path`."""
    pts = [(p[0], X0 + p[1] * G, Y0 + p[2] * G) for p in path]
    need = CLR + half + SLACK + 0.02
    ripped = set()
    for t in list(TRACK_OBJS):
        if t.GetNetname() == net:
            continue
        if t.Type() == pcbnew.PCB_VIA_T:
            x, y = mm(t.GetPosition().x), mm(t.GetPosition().y)
            r = mm(t.GetWidth(F)) / 2
            hit = any(math.hypot(px - x, py - y) < need + r for _, px, py in pts)
        else:
            s_, e_ = t.GetStart(), t.GetEnd()
            x1, y1, x2, y2, r = mm(s_.x), mm(s_.y), mm(e_.x), mm(e_.y), mm(t.GetWidth()) / 2
            lay = t.GetLayer()
            hit = any(l == lay and dist_pt_seg(px, py, x1, y1, x2, y2) < need + r for l, px, py in pts)
        if hit:
            ripped.add(t.GetNetname())
            DEAD.append(t)
            TRACK_OBJS.remove(t)
    return ripped


# 1. join split clusters of ordinary nets
import os
SKIP = set(filter(None, os.environ.get('SKIP_NETS', '').split(',')))
CHANGED = [False]
for ROUND in range(6):
    CHANGED[0] = False
    for net in sig_nets:
        if net in PLANES or net in SKIP:
            continue
        for _ in range(8):
            its = items()
            cl = clusters(net, its)
            if len(cl) < 2:
                break
            cl.sort(key=len)
            a = cl[0]
            ok = False
            for width in (0.2, 0.15, 0.13):
                grids, gv = obstacle_maps(net, its, width / 2)
                src = seeds(a)
                src_set = set(src)
                free_set = pad_escape(a, grids)
                tgt = set()
                for c in cl[1:]:
                    pe = pad_escape(c, grids)
                    tgt |= pe | set(seeds(c))
                    free_set |= pe
                path = astar(src, lambda l, x, y: (l, x, y) in tgt, grids, gv)
                if path:
                    emit(path, net, width)
                    report.append(f"joined {net} ({len(path)} cells, w={width})")
                    ok = True
                    CHANGED[0] = True
                    break
            if not ok and ROUND < 4:
                width = 0.2
                grids, gv = obstacle_maps(net, its, width / 2)
                hard, _ = obstacle_maps(net, its, width / 2, hard_only=True)
                path = astar(src, lambda l, x, y: (l, x, y) in tgt, grids, gv, hard=hard)
                if path:
                    ripped = rip_blockers(path, net, width / 2)
                    emit(path, net, width)
                    report.append(f"joined {net} after ripping parts of {sorted(ripped)}")
                    CHANGED[0] = True
                    ok = True
            if not ok:
                report.append(f"FAILED to join {net}: {len(cl)} clusters, explored {LAST[0]} cells from {[ (i.get('ref'),i.get('num'),i['kind'],i['c']) for i in a][:4]}")
                break


    if not CHANGED[0]:
        break

# 1b. plane-net clusters that sit outside their plane get a track to the rest
for net in ("VBUS", "+5V_STRIP"):
    for _ in range(6):
        its = items()
        cl = clusters(net, its)
        out = [c for c in cl if not any(in_plane(net, *i["c"]) for i in c)]
        rest = [c for c in cl if c not in out]
        if not out or not rest:
            break
        a = out[0]
        ok = False
        for width in (0.4, 0.3, 0.2):
            grids, gv = obstacle_maps(net, its, width / 2)
            src = seeds(a)
            src_set = set(src)
            free_set = pad_escape(a, grids)
            tgt = set()
            for c in rest:
                pe = pad_escape(c, grids)
                tgt |= pe | set(seeds(c))
                free_set |= pe
            path = astar(src, lambda l, x, y: (l, x, y) in tgt, grids, gv)
            if path:
                emit(path, net, width)
                report.append(f"joined {net} outlier ({len(path)} cells, w={width})")
                ok = True
                break
        if not ok:
            report.append(f"FAILED to join {net} outlier")
            break

# 2. plane nets: every cluster gets a via inside its plane; heavy pads get a second one
def ckey(c):
    return tuple(sorted((round(i["c"][0], 2), round(i["c"][1], 2)) for i in c if i["kind"] == "pad"))[:6]


for net in ("VBUS", "+5V_STRIP", "GND"):
    skip = set()
    for _ in range(150):
        its = items()
        cl = clusters(net, its)
        todo = None
        for c in cl:
            k = ckey(c)
            has = any(i["pth"] and in_plane(net, *i["c"]) for i in c)
            heavy = [i for i in c if i["kind"] == "pad" and (i["ref"], i["num"]) in HEAVY]
            nvia = sum(1 for i in c if i["kind"] == "via" and in_plane(net, *i["c"]))
            if not has and (k, 0) not in skip:
                todo = (c, None, (k, 0))
                break
            want = 2 * len({i["ref"] for i in heavy})
            if heavy and nvia < want and (k, nvia) not in skip:
                todo = (c, heavy, (k, nvia))
                break
        if todo is None:
            break
        c, heavy, key = todo
        skip.add(key)
        ok = False
        own_smd = [i["g"] for i in its if i["net"] == net and i["kind"] == "pad" and not i["pth"]]
        own_vias = [i["c"] for i in its if i["net"] == net and i["pth"]]
        for width in ((0.5, 0.3, 0.2) if net != "GND" else (0.3, 0.2)):
            grids, gv = obstacle_maps(net, its, width / 2)
            start = heavy if heavy else c
            src = [s for s in seeds(start) if s[0] == F] or seeds(start)
            src_set = set()
            free_set = pad_escape(c, grids)

            def goal(l, x, y):
                px, py = X0 + x * G, Y0 + y * G
                if l != F or gv[y * NX + x] or grids[B][y * NX + x]:
                    return False
                if not in_plane(net, px, py):
                    return False
                for r in own_smd:
                    if r[1] - 0.32 < px < r[3] + 0.32 and r[2] - 0.32 < py < r[4] + 0.32:
                        return False
                return all(math.hypot(px - ox, py - oy) >= 0.95 for ox, oy in own_vias)
            path = astar(src, goal, grids, gv, allow_via=False, max_nodes=250000)
            if path:
                if len(path) > 1:
                    emit(path, net, width)
                add_via(path[-1][1], path[-1][2], net)
                ok = True
                break
        tag = ",".join(sorted({i["ref"] + "." + i["num"] for i in c if i["kind"] == "pad"}))[:60]
        if not ok and len(cl) > 1:
            for width in (0.3, 0.2, 0.15):
                grids, gv = obstacle_maps(net, its, width / 2)
                src = seeds(c)
                src_set = set(src)
                free_set = pad_escape(c, grids)
                tgt = set()
                for o in cl:
                    if o is not c:
                        pe = pad_escape(o, grids)
                        tgt |= pe
                        free_set |= pe
                path = astar(src, lambda l, x, y: (l, x, y) in tgt, grids, gv)
                if path:
                    emit(path, net, width)
                    report.append(f"joined {net} [{tag}] by track instead of a via")
                    ok = True
                    break
            if ok:
                continue
        report.append(("via   " if ok else "FAILED via ") + f"{net} for [{tag}]")

print("\n".join(report))
for t in DEAD:
    b.Remove(t)
pcbnew.SaveBoard(PCB, b)
print('saved, removed', len(DEAD))
sys.stdout.flush()
import os as _os
_os._exit(0)
print("\n".join(report))
