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
LON0, LAT0, X0, Y0 = 139.7578, 35.6957, 980, 280   # A7出口のあたりを (X0, Y0) に置く。ルートの東の端が右端の少し手前に来る
KX = PXM * 111320 * math.cos(math.radians(LAT0))
KY = PXM * 110950


def xy(p):
    return (X0 + (p["lon"] - LON0) * KX, Y0 - (p["lat"] - LAT0) * KY)


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


def nodes_of(name, lo, hi):
    """名前の道の点を経度 lo〜hi で集め、上下線のずれをならして西から東へ並べる。"""
    pts = [p for e in data if e["tags"].get("name") == name and "highway" in e["tags"] for p in e["geometry"] if lo <= p["lon"] <= hi]
    buckets = {}
    for p in pts:
        buckets.setdefault(round(p["lon"] / 0.0003), []).append(p)
    out_ = []
    for k in sorted(buckets):
        b = buckets[k]
        south = min(b, key=lambda p: p["lat"])          # 南側の車線（A7出口と古書店の側）にそろえる
        out_.append(south)
    return out_


# ルート：A7出口 → 靖国通りを東へ（古書店街）→ 駿河台下（三省堂）で南へ → すずらん通りを西へ → 神田伯剌西爾
# 靖国通りの南側の車線（駿河台下 → 神保町の向き）を、点の並びのまま逆にたどる
yasu_way = next(e for e in data if e["tags"].get("name") == "靖国通り" and e["geometry"][0]["lon"] > 139.7613 and e["geometry"][-1]["lon"] < 139.7582)
yasu = [{"lon": 139.7579, "lat": 35.6959}] + [p for p in yasu_way["geometry"][::-1] if p["lon"] > 139.7580]
suzu = [p for p in next(e for e in data if e["tags"].get("name") == "神田すずらん通り")["geometry"] if p["lon"] >= 139.7600]
route_pts = simplify([xy(p) for p in yasu] + [xy(p) for p in suzu[1:]], 0.8)
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


index = ROOT / "index.html"
html = index.read_text()
new = re.sub(r'<svg class="bgmap".*?</svg>', lambda m: svg(), html, flags=re.S)
if 'class="bgmap"' not in html:
    raise SystemExit('index.html に背景の地図の置き場（class="bgmap" の svg）がありません')
index.write_text(new)
print("roads", len(roads), "start", start, "goal", goal, "crop", crop)
