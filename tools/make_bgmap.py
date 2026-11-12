"""「なぜ歩くのか」の背景の地図（横幅いっぱい）を作り、index.html に書き込む。

元の地図の絵（480×360）を右寄りの位置にそのまま置き、外側の道・区画・川・線路・水彩を描き足す。
スタートとゴールの点は元の位置のまま。使い方: python3 tools/make_bgmap.py
"""
import random
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
W, H = 1440, 600
OX, OY = 760, 110          # 元の絵を置く位置（ルートは画面の中央より右に来る）
random.seed(21)


def nums(d):
    return [float(v) for v in re.findall(r"-?\d+(?:\.\d+)?", d)]


def shift(d, dx=OX, dy=OY):
    """パスの座標を (dx, dy) だけずらす（M・C・L・H・V の絶対座標だけを使っている前提）。"""
    out, cmd, i = [], None, 0
    for tok in re.findall(r"[MCLHVZ]|-?\d+(?:\.\d+)?", d):
        if tok.isalpha():
            cmd, i = tok, 0
            out.append(tok)
            continue
        v = float(tok)
        if cmd in "MCL":
            v += dx if i % 2 == 0 else dy
        elif cmd == "H":
            v += dx
        elif cmd == "V":
            v += dy
        i += 1
        out.append(f"{v:g}")
    return " ".join(out)


# 元の絵の道（480×360 の座標）。(パス, 太さ, 向き)
ORIG_ROADS = [
    ("M-10 150 C80 160 160 150 240 146 C320 142 400 134 490 120", 11, "h"),
    ("M170 -10 C176 80 182 160 176 230 C172 280 166 320 160 370", 9, "v"),
    ("M330 -10 C320 60 316 120 322 180 C326 230 336 280 344 370", 6, "v"),
    ("M-10 92 C70 88 140 86 210 82 C270 79 330 70 400 54", 4, "h"),
    ("M40 -10 C46 60 52 140 60 220 C64 260 70 300 76 330", 4, "v"),
    ("M70 236 C140 228 210 224 262 226 C300 228 330 240 380 238 C420 236 450 230 490 226", 5, "h"),
    ("M240 146 C248 180 252 200 262 226", 3, ""),
    ("M410 40 C412 110 418 170 430 230", 3, ""),
    ("M100 160 C104 190 108 210 112 232", 2.5, ""),
    ("M210 82 C214 110 220 128 228 147", 2.5, ""),
    ("M130 60 C134 90 138 120 140 150", 2.5, ""),
    ("M262 226 C266 260 270 290 276 330", 2.5, ""),
    ("M330 180 C360 182 390 186 420 184", 2.5, ""),
    ("M20 120 C50 118 80 116 110 114", 2.5, ""),
    ("M360 70 C364 100 368 120 372 140", 2, ""),
    ("M200 190 C222 188 240 190 262 192", 2, ""),
    ("M100 280 C140 276 170 272 200 270", 2, ""),
]


def wobble(x0, y0, x1, y1, amp=10):
    """2点をゆるく曲がった線でつなぐ（手描きの道のように）。"""
    mx, my = (x0 + x1) / 2, (y0 + y1) / 2
    if abs(x1 - x0) > abs(y1 - y0):
        c1 = (x0 + (x1 - x0) / 3, y0 + random.uniform(-amp, amp))
        c2 = (x0 + 2 * (x1 - x0) / 3, y1 + random.uniform(-amp, amp))
    else:
        c1 = (x0 + random.uniform(-amp, amp), y0 + (y1 - y0) / 3)
        c2 = (x1 + random.uniform(-amp, amp), y0 + 2 * (y1 - y0) / 3)
    return f"C{c1[0]:.0f} {c1[1]:.0f} {c2[0]:.0f} {c2[1]:.0f} {x1:.0f} {y1:.0f}"


roads = []  # (d, 太さ)
for d, w, kind in ORIG_ROADS:
    n = nums(d)
    sx, sy, ex, ey = n[0] + OX, n[1] + OY, n[-2] + OX, n[-1] + OY
    body = shift(d)
    if kind == "h":
        # 左は画面の端まで、右も端まで道をのばす
        ly = sy + random.uniform(-14, 14)
        left = f"M-30 {ly:.0f} " + wobble(-30, ly, sx, sy)
        right = wobble(ex, ey, W + 30, ey + random.uniform(-20, 10))
        roads.append((left + " L" + body[1:] + " " + right, w))
    elif kind == "v":
        top = f"M{sx + random.uniform(-10, 10):.0f} -30 " + wobble(sx, -30, sx, sy)
        bottom = wobble(ex, ey, ex + random.uniform(-14, 14), H + 30)
        roads.append((top + " L" + body[1:] + " " + bottom, w))
    else:
        roads.append((body, w))

# 左側と右端に新しい道を足す（元の絵の外側）
for x in [70, 190, 330, 470, 600, 1290, 1390]:
    w = random.choice([4, 5, 9]) if x in (330, 1290) else random.choice([2.5, 3, 4])
    d = f"M{x + random.uniform(-10, 10):.0f} -30 " + wobble(x, -30, x + random.uniform(-20, 20), H / 2, 14) + " " + wobble(x, H / 2, x + random.uniform(-20, 20), H + 30, 14)
    roads.append((d, w))
for y in [60, 380, 470]:
    w = 6 if y == 380 else 3
    roads.append((f"M-30 {y} " + wobble(-30, y, OX - 10, y + random.uniform(-16, 16), 12), w))
for y in [500]:
    roads.append((f"M{OX + 60} {y} " + wobble(OX + 60, y, W + 30, y - 10, 10), 3))
# 小さな路地
for _ in range(18):
    x = random.uniform(20, OX - 60)
    y = random.uniform(40, H - 60)
    if random.random() < .5:
        roads.append((f"M{x:.0f} {y:.0f} " + wobble(x, y, x + random.uniform(50, 110), y + random.uniform(-6, 6), 4), 2))
    else:
        roads.append((f"M{x:.0f} {y:.0f} " + wobble(x, y, x + random.uniform(-6, 6), y + random.uniform(50, 110), 4), 2))
for _ in range(6):
    x = random.uniform(OX + 480, W - 30)
    y = random.uniform(40, H - 60)
    roads.append((f"M{x:.0f} {y:.0f} " + wobble(x, y, x + random.uniform(-6, 6), y + random.uniform(50, 100), 4), 2))

# 建物の小さなかたまり
blocks = []
ORIG_BLOCKS = [(190, 100, 14, 10), (208, 98, 10, 12), (260, 160, 16, 11), (280, 163, 10, 9), (80, 190, 12, 14), (120, 120, 14, 10),
               (350, 150, 12, 12), (200, 250, 16, 10), (146, 58, 12, 9), (240, 100, 10, 12), (300, 100, 14, 10), (390, 200, 12, 12),
               (120, 250, 16, 10), (60, 130, 12, 9), (420, 150, 10, 12), (250, 280, 14, 10)]
for x, y, w, h in ORIG_BLOCKS:
    blocks.append((x + OX, y + OY, w, h))
for _ in range(46):
    x = random.choice([random.uniform(10, OX - 20), random.uniform(OX + 470, W - 20)])
    y = random.uniform(30, H - 40)
    blocks.append((x, y, random.choice([10, 12, 14, 16]), random.choice([9, 10, 12])))

wash = [
    # 元の絵の水彩
    shift("M20 60 C120 10 330 0 440 50 C500 90 490 270 430 320 C340 370 120 365 50 310 C0 270 -20 120 20 60Z"),
    shift("M110 100 C190 70 320 80 370 130 C410 175 380 250 300 262 C220 274 130 250 105 200 C90 165 85 115 110 100Z"),
    # 左に広げる
    "M-40 120 C80 40 300 30 520 70 C700 100 820 160 800 300 C780 440 600 520 380 520 C160 520 -20 480 -40 380Z",
    "M60 200 C160 150 320 160 420 210 C500 250 480 340 400 370 C300 410 150 400 90 340 C40 290 20 230 60 200Z",
    "M1180 40 C1300 20 1460 60 1470 200 C1480 360 1400 520 1260 540 C1160 556 1120 460 1150 360 C1170 280 1120 80 1180 40Z",
]
wash_fill = ["var(--wash-3)", "var(--wash-1)", "var(--wash-3)", "var(--wash-1)", "var(--wash-3)"]
parks = [shift("M300 200 C330 190 372 196 382 222 C390 246 362 262 334 258 C306 254 288 236 290 218 C291 208 294 203 300 200Z"),
         "M220 300 C260 286 320 292 330 322 C338 350 300 366 262 362 C226 358 206 336 210 318 C212 308 214 304 220 300Z"]
river = "M-30 470 C120 452 260 470 420 486 C560 500 700 470 " + f"{OX - 10} {OY + 300} " + shift("C70 280 120 300 180 318 C240 336 300 330 360 340 C410 348 450 360 500 356") + f" C{OX + 600} {OY + 352} {W - 60} {OY + 330} {W + 30} {OY + 336}"
rail = "M-30 150 C200 140 500 128 " + f"{OX - 10} {OY + 40} " + shift("C120 30 260 22 490 10") + f" C{OX + 600} {OY + 6} {W - 80} {OY - 4} {W + 30} {OY - 8}"
route = shift("M70 236 C110 232 140 230 176 226 C178 200 178 176 178 150 C200 148 220 146 240 146 C280 144 300 142 322 140")
start, goal = (70 + OX, 236 + OY), (322 + OX, 140 + OY)

parts = [
    f'<svg class="bgmap" viewBox="0 0 {W} {H}" preserveAspectRatio="xMidYMid slice" aria-hidden="true" data-route="{start[0] - 60} {goal[1] - 120} {goal[0] - start[0] + 120} {start[1] - goal[1] + 220}">',
    '<defs><filter id="wash" x="-10%" y="-10%" width="120%" height="120%"><feTurbulence type="fractalNoise" baseFrequency="0.012" numOctaves="3" seed="7" result="n"/>'
    '<feDisplacementMap in="SourceGraphic" in2="n" scale="40" xChannelSelector="R" yChannelSelector="G" result="d"/><feGaussianBlur in="d" stdDeviation="3"/></filter></defs>',
    '<g filter="url(#wash)">' + "".join(f'<path d="{d}" fill="{c}"/>' for d, c in zip(wash, wash_fill)) + "".join(f'<path d="{p}" fill="var(--map-park)"/>' for p in parks) + "</g>",
    f'<path d="{river}" fill="none" stroke="var(--map-water)" stroke-width="20" stroke-linecap="round"/>',
    '<g fill="none" stroke="var(--white)" stroke-linecap="round" stroke-linejoin="round">' + "".join(f'<path d="{d}" stroke-width="{w}"/>' for d, w in roads) + "</g>",
    f'<path d="{rail}" fill="none" stroke="var(--ink-soft)" stroke-width="1.5" opacity=".5"/><path d="{rail}" fill="none" stroke="var(--ink-soft)" stroke-width="6" stroke-dasharray="1.5 9" opacity=".4"/>',
    '<g fill="var(--map-block)" opacity=".7">' + "".join(f'<rect x="{x:.0f}" y="{y:.0f}" width="{w}" height="{h}" rx="1.5"/>' for x, y, w, h in blocks) + "</g>",
    f'<path d="{route}" fill="none" stroke="var(--green)" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/>',
    f'<circle cx="{start[0]}" cy="{start[1]}" r="6.5" fill="var(--green)"/>',
    f'<circle cx="{goal[0]}" cy="{goal[1]}" r="7" fill="var(--paper)" stroke="var(--green)" stroke-width="3"/>',
    "</svg>",
]
svg = "\n".join(parts)
index = ROOT / "index.html"
s = index.read_text()
s2 = re.sub(r'<svg class="bgmap".*?</svg>', svg, s, flags=re.S)
if s2 == s and 'class="bgmap"' not in s:
    raise SystemExit("index.html に背景の地図の置き場（class=\"bgmap\" の svg）がありません")
index.write_text(s2)
print("wrote bgmap", len(svg))
