"""最後の予約欄（緑の帯）の地に敷く等高線の SVG を作り、index.html の svg.contours を書き換える（見本 m5）。

等高線は数式で作る：1つの山につき、少しゆがんだ入れ子の閉じた曲線を5本（Catmull-Rom を3次ベジェにしてなめらかにする）。
帯の右上に山、左下に窪みを1つずつ置き、中央の文字の後ろは CSS のマスクで消す。
線は外側から順に描くので、外側の線ほど --contour-i が小さい。各山の内から4本目は計曲線（class="idx"）として少し濃く太くする。
乱数の種を固定しているので、何度実行しても同じ線になる。

使い方: python3 tools/make_contours.py
"""
import math
import pathlib
import random
import re

SITE = pathlib.Path(__file__).resolve().parent.parent
INDEX = SITE / "index.html"
W, H = 1200, 600


def catmull_rom_closed(pts):
    n = len(pts)
    f = lambda v: str(round(v))
    d = [f"M{f(pts[0][0])} {f(pts[0][1])}"]
    for i in range(n):
        p0, p1, p2, p3 = pts[(i - 1) % n], pts[i], pts[(i + 1) % n], pts[(i + 2) % n]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d.append(f"C{f(c1[0])} {f(c1[1])} {f(c2[0])} {f(c2[1])} {f(p2[0])} {f(p2[1])}")
    return "".join(d) + "Z"


def hill(cx, cy, rings, r0, step, sx, sy, rot, drift, seed, start_angle):
    """1つの山の等高線。内側ほど丸く、外側ほどゆがむ。中心は内側に向かって少しずれる（山頂が偏る）。"""
    rnd = random.Random(seed)
    # 全部の輪で共通のゆらぎ（入れ子の形をそろえて、線が交わらないようにする）
    common = [(rnd.uniform(.035, .07) / (i * .55), rnd.uniform(0, 2 * math.pi)) for i in range(2, 6)]
    out = []
    for k in range(rings):
        r = r0 + k * step
        own = [(rnd.uniform(.006, .014), rnd.uniform(0, 2 * math.pi)) for _ in range(2, 5)]
        amp = .55 + .45 * k / max(1, rings - 1)  # 外側ほどゆがみが大きい
        ox = cx + (rings - 1 - k) * drift[0]
        oy = cy + (rings - 1 - k) * drift[1]
        n = 24 + int(r / 25)
        pts = []
        for j in range(n):
            t = start_angle + 2 * math.pi * j / n
            g = sum(a * math.sin(i * t + p) for i, (a, p) in zip(range(2, 6), common)) * amp
            g += sum(a * math.sin(i * t + p) for i, (a, p) in zip(range(2, 5), own))
            rr = r * (1 + g)
            x, y = rr * sx * math.cos(t), rr * sy * math.sin(t)
            c, s = math.cos(rot), math.sin(rot)
            pts.append((ox + x * c - y * s, oy + x * s + y * c))
        out.append(catmull_rom_closed(pts))
    return out


def build():
    # 右上の山と左下の窪みに5本ずつ（合わせて10本）。外側の線から描く（狭い画面では外側の線しか見えないため）
    a = hill(1035, 95, 5, 44, 64, 1.3, .82, math.radians(-14), (7, 4), 11, math.radians(200))
    b = hill(150, 560, 5, 40, 64, 1.4, .78, math.radians(18), (-6, -4), 29, math.radians(-30))
    paths = []
    order = 0
    for k in reversed(range(max(len(a), len(b)))):
        for lst in (a, b):
            if k < len(lst):
                attr = ' class="idx"' if k == 3 else ""
                paths.append(f'<path{attr} style="--contour-i:{order}" d="{lst[k]}" pathLength="1"/>')
                order += 1
    return (f'<svg class="contours" viewBox="0 0 {W} {H}" preserveAspectRatio="xMidYMid slice" aria-hidden="true" focusable="false">'
            '<g fill="none" stroke-linecap="round" stroke-linejoin="round">' + "".join(paths) + "</g></svg>")


def main():
    svg = build()
    src = INDEX.read_text(encoding="utf-8")
    old = re.compile(r'<svg class="contours".*?</svg>', re.S)
    if old.search(src):
        src = old.sub(lambda m: svg, src, count=1)
    else:
        head = '<section class="section closing" id="reserve">'
        if head not in src:
            raise SystemExit("index.html に最後の予約欄（#reserve）が見つかりません")
        src = src.replace(head, head + "\n  " + svg, 1)
    INDEX.write_text(src, encoding="utf-8")
    print(f"contours: {svg.count('<path')} paths, {len(svg)} bytes")


if __name__ == "__main__":
    main()
