"""「なぜ歩くのか」の背景の地図を、OpenStreetMap の神保町のデータから水彩の描き方で作り、index.html の svg.bgmap を書き換える。
データは tools/data/jimbocho-osm.json（Overpass API で取った道・川・公園。© OpenStreetMap contributors、ODbL）。
道は名前のある通りと住宅街の道だけ（建物の間の通路は外す）を、なめらかな曲線で描く。2026-11-12 に黒田さんが見本の案2を選んだ。
使い方: python3 -I tools/make_osmmap.py
"""
import json
import re
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
src = ROOT / "tools/data/jimbocho-osm.json"
data = json.loads(src.read_text())["elements"]

W, H = 1440, 600
PXM = 1.25                                  # 1m あたりのピクセル
LAT0 = 35.6957
KX = PXM * 111320 * math.cos(math.radians(LAT0))
KY = PXM * 110950
RIGHT, MIDY, MAXW = 1370, 300, 380      # ルートの東の端を x=RIGHT に、上下のまん中を y=MIDY に置く（右端の少し手前。xMaxYMid で切り出すので狭い画面でも切れない）
ORIGIN = [139.7578, LAT0, 980, 280]


def xy(p):
    lon0, lat0, x0, y0 = ORIGIN
    return (x0 + (p["lon"] - lon0) * KX, y0 - (p["lat"] - lat0) * KY)


def simplify(pts, tol=1.2):
    if len(pts) < 3:
        return pts
    (x0, y0), (x1, y1) = pts[0], pts[-1]
    dx, dy = x1 - x0, y1 - y0
    L = math.hypot(dx, dy) or 1e-9
    far, idx = 0, 0
    for i, (x, y) in enumerate(pts[1:-1], 1):
        d = abs(dy * x - dx * y + x1 * y0 - y1 * x0) / L
        if d > far:
            far, idx = d, i
    if far <= tol:
        return [pts[0], pts[-1]]
    return simplify(pts[: idx + 1], tol)[:-1] + simplify(pts[idx:], tol)


def d_of(pts, close=False):
    s = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts)
    return s + ("Z" if close else "")


def smooth_d(pts, close=False):
    """点の並びを、角のないなめらかな曲線（Catmull-Rom を3次ベジェにしたもの）にする。"""
    if len(pts) < 3:
        return d_of(pts, close)
    p = [pts[0]] + list(pts) + [pts[-1]]
    s = f"M{pts[0][0]:.1f} {pts[0][1]:.1f}"
    for i in range(1, len(p) - 2):
        (x0, y0), (x1, y1), (x2, y2), (x3, y3) = p[i - 1], p[i], p[i + 1], p[i + 2]
        s += f" C{x1 + (x2 - x0) / 6:.1f} {y1 + (y2 - y0) / 6:.1f} {x2 - (x3 - x1) / 6:.1f} {y2 - (y3 - y1) / 6:.1f} {x2:.1f} {y2:.1f}"
    return s + ("Z" if close else "")


def visible(pts, m=80):
    return any(-m < x < W + m and -m < y < H + m for x, y in pts)


WIDTH = {"primary": 12, "secondary": 9, "tertiary": 6, "unclassified": 3.5, "residential": 3.5,
         "living_street": 2.5, "pedestrian": 2.5, "service": 1.4}
# 歩く道筋。道のつながり（OpenStreetMap の道の点）をたどった最短の道で、経由点を順につなぐ
ROUTES = {
    # 古書店街をまっすぐ：A7出口から靖国通りを東へ、駿河台下（三省堂書店）まで
    "yasukuni": [(139.7579, 35.6959), (139.7606, 35.69593)],
    # すずらん通りを抜ける：A7出口から白山通りを少し南へ、すずらん通りを東へ、駿河台下まで
    "suzuran": [(139.7577, 35.6957), (139.75824, 35.69531), (139.7600, 35.69537), (139.76132, 35.69546)],
    # お茶の水から下る：明治大学のあたりから明大通りの坂を下り、駿河台下からすずらん通りを西へ、神田伯剌西爾のあたりまで
    "meidai": [(139.7620, 35.6978), (139.76132, 35.69546), (139.7600, 35.69537)],
}
ROUTE = "suzuran"   # 2026-11-12 黒田さんが見本の案2を選んだ

WALKABLE = {"primary", "secondary", "tertiary", "unclassified", "residential", "living_street", "pedestrian"}


def graph():
    g = {}
    for e in data:
        if e["tags"].get("highway") not in WALKABLE:
            continue
        pts = [(round(p["lon"], 6), round(p["lat"], 6)) for p in e["geometry"]]
        for a_, b_ in zip(pts, pts[1:]):
            d = math.hypot((a_[0] - b_[0]) * 90400, (a_[1] - b_[1]) * 110950)
            g.setdefault(a_, []).append((b_, d))
            g.setdefault(b_, []).append((a_, d))
    return g


def shortest(g, a_, b_):
    import heapq
    near = lambda q: min(g, key=lambda n: (n[0] - q[0]) ** 2 * 0.66 + (n[1] - q[1]) ** 2)
    s0, t0 = near(a_), near(b_)
    dist, prev, pq = {s0: 0}, {}, [(0, s0)]
    while pq:
        d, n = heapq.heappop(pq)
        if n == t0:
            break
        if d > dist.get(n, 1e18):
            continue
        for m, w in g[n]:
            if d + w < dist.get(m, 1e18):
                dist[m], prev[m] = d + w, n
                heapq.heappush(pq, (d + w, m))
    path = [t0]
    while path[-1] != s0:
        path.append(prev[path[-1]])
    return path[::-1]


def despike(pts, limit=100):
    """上下線を乗り換えたときにできる、行って戻る小さな折り返しを取りのぞく。"""
    pts = list(pts)
    changed = True
    while changed and len(pts) > 2:
        changed = False
        for i in range(1, len(pts) - 1):
            (x0, y0), (x1, y1), (x2, y2) = pts[i - 1], pts[i], pts[i + 1]
            a1, a2 = math.atan2(y1 - y0, x1 - x0), math.atan2(y2 - y1, x2 - x1)
            turn = abs((math.degrees(a2 - a1) + 180) % 360 - 180)
            if turn > limit or math.hypot(x1 - x0, y1 - y0) < 4:
                del pts[i]
                changed = True
                break
    return pts


def route_lonlat(name):
    g = graph()
    wp = ROUTES[name]
    out_ = []
    for a_, b_ in zip(wp, wp[1:]):
        seg = shortest(g, a_, b_)
        out_ += seg if not out_ else seg[1:]
    return [{"lon": x, "lat": y} for x, y in out_]


def build(name):
    """ルートを決め、ルートが右寄りに来るように地図の位置を合わせてから、道・川・公園を描く位置に直す。"""
    global roads, rivers, waters, parks, rails, route_pts, start, goal, route_d, crop, WASH
    global KX, KY
    ll = route_lonlat(name)
    # 長いルートは縮めて、幅が MAXW に収まるようにする（狭い画面でスタートが文章のカードに隠れないように）
    span = (max(p["lon"] for p in ll) - min(p["lon"] for p in ll)) * 111320 * math.cos(math.radians(LAT0))
    pxm = min(PXM, MAXW / span)
    KX, KY = pxm * 111320 * math.cos(math.radians(LAT0)), pxm * 110950
    ORIGIN[:] = [139.7578, LAT0, 0, 0]
    pts0 = [xy(p) for p in ll]
    ORIGIN[2] = RIGHT - max(x for x, _ in pts0)
    ORIGIN[3] = MIDY - (min(y for _, y in pts0) + max(y for _, y in pts0)) / 2
    roads, rivers, waters, parks, rails = [], [], [], [], []
    for e in data:
        t = e["tags"]
        pts = [xy(p) for p in e["geometry"]]
        if not visible(pts):
            continue
        if "highway" in t:
            roads.append((t["highway"], t.get("name", ""), simplify(pts, 2)))
        elif t.get("waterway") == "river":
            rivers.append(simplify(pts))
        elif t.get("natural") == "water":
            waters.append(simplify(pts))
        elif t.get("leisure") == "park":
            parks.append(simplify(pts))
        elif "railway" in t:
            rails.append(simplify(pts))


    route_pts = simplify(despike([xy(p) for p in ll]), 2.5)
    start, goal = route_pts[0], route_pts[-1]
    route_d = smooth_d(route_pts)

    rx0 = min(x for x, _ in route_pts)
    rx1 = max(x for x, _ in route_pts)
    ry0 = min(y for _, y in route_pts)
    ry1 = max(y for _, y in route_pts)
    crop = (rx0 - 90, ry0 - 150, rx1 - rx0 + 180, (rx1 - rx0 + 180) * 3 / 4)

    WASH = [
        ("M-60 -40 L1500 -40 L1500 640 L-60 640Z", "var(--wash-3)"),
        (f"M{rx0 - 160:.0f} {ry0 - 120:.0f} C{rx0 + 40:.0f} {ry0 - 200:.0f} {rx1 + 60:.0f} {ry0 - 180:.0f} {rx1 + 150:.0f} {ry0 - 60:.0f} "
         f"C{rx1 + 230:.0f} {ry0 + 40:.0f} {rx1 + 120:.0f} {ry1 + 170:.0f} {rx1 - 60:.0f} {ry1 + 190:.0f} "
         f"C{rx0 + 100:.0f} {ry1 + 220:.0f} {rx0 - 200:.0f} {ry1 + 160:.0f} {rx0 - 200:.0f} {ry1 + 40:.0f} "
         f"C{rx0 - 210:.0f} {ry0 - 20:.0f} {rx0 - 190:.0f} {ry0 - 100:.0f} {rx0 - 160:.0f} {ry0 - 120:.0f}Z", "var(--wash-1)"),
        ("M-40 60 C120 20 360 40 520 110 C640 170 620 330 500 400 C360 470 120 470 0 420 C-80 380 -100 120 -40 60Z", "var(--wash-1)"),
    ]




def svg(uid=""):
    keep = lambda h: h != "service"
    order = ["service", "pedestrian", "living_street", "residential", "unclassified", "tertiary", "secondary", "primary"]
    rs = sorted([r for r in roads if keep(r[0])], key=lambda r: order.index(r[0]) if r[0] in order else 0)
    parts = [
        f'<svg class="bgmap" viewBox="0 0 {W} {H}" preserveAspectRatio="xMaxYMid slice" aria-hidden="true" data-route="{crop[0]:.0f} {crop[1]:.0f} {crop[2]:.0f} {crop[3]:.0f}">',
        f'<defs><filter id="wash{uid}" x="-10%" y="-10%" width="120%" height="120%"><feTurbulence type="fractalNoise" baseFrequency="0.012" numOctaves="3" seed="7" result="n"/>'
        f'<feDisplacementMap in="SourceGraphic" in2="n" scale="40" xChannelSelector="R" yChannelSelector="G" result="d"/><feGaussianBlur in="d" stdDeviation="3"/></filter>'
        '</defs>',
        f'<g filter="url(#wash{uid})">' + "".join(f'<path d="{d}" fill="{c}"/>' for d, c in WASH)
        + "".join(f'<path d="{smooth_d(p, True)}" fill="var(--map-park)"/>' for p in parks)
        + "".join(f'<path d="{smooth_d(p, True)}" fill="var(--map-water)"/>' for p in waters) + "</g>",
        '<g fill="none" stroke="var(--map-water)" stroke-width="16" stroke-linecap="round" stroke-linejoin="round">' + "".join(f'<path d="{smooth_d(p)}"/>' for p in rivers) + "</g>",
        f'<g fill="none" stroke="var(--white)" stroke-linecap="round" stroke-linejoin="round" >'
        + "".join(f'<path d="{smooth_d(p)}" stroke-width="{WIDTH.get(h, 2)}"/>' for h, _, p in rs) + "</g>",
        "".join(f'<path d="{d_of(p)}" fill="none" stroke="var(--ink-soft)" stroke-width="1.5" opacity=".5"/><path d="{d_of(p)}" fill="none" stroke="var(--ink-soft)" stroke-width="6" stroke-dasharray="1.5 9" opacity=".4"/>' for p in rails),
    ]
    parts += [
        f'<path d="{route_d}" fill="none" stroke="var(--green)" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/>',
        f'<circle cx="{start[0]:.1f}" cy="{start[1]:.1f}" r="6.5" fill="var(--green)"/>',
        f'<circle cx="{goal[0]:.1f}" cy="{goal[1]:.1f}" r="7" fill="var(--paper)" stroke="var(--green)" stroke-width="3"/>',
        "</svg>",
    ]
    return "\n".join(parts)


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else ROUTE)
    index = ROOT / "index.html"
    html = index.read_text()
    if 'class="bgmap"' not in html:
        raise SystemExit('index.html に背景の地図の置き場（class="bgmap" の svg）がありません')
    index.write_text(re.sub(r'<svg class="bgmap".*?</svg>', lambda m: svg(), html, flags=re.S))
    print("route", sys.argv[1] if len(sys.argv) > 1 else ROUTE, "roads", len(roads), "start", start, "goal", goal, "crop", crop)
