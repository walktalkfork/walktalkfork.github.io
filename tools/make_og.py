"""共有画像（assets/ogp.png、1200×630）を作る。

書体は tools/fonts/ShipporiMincho-Medium.ttf（Google Fonts、OFL）。なければ
https://github.com/google/fonts/raw/main/ofl/shipporimincho/ShipporiMincho-Medium.ttf から取ってくる。
使い方（Pillow が入った Python で）: python tools/make_og.py
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
FONT = ROOT / "tools/fonts/ShipporiMincho-Medium.ttf"
PAPER, INK, SOFT, GREEN = "#F4F0E6", "#22201C", "#5B564D", "#2F5D4A"
W, H, S = 1200, 630, 2  # 2倍で描いて縮める

img = Image.new("RGB", (W * S, H * S), PAPER)
d = ImageDraw.Draw(img)
title = ImageFont.truetype(str(FONT), 112 * S)
sub = ImageFont.truetype(str(FONT), 40 * S)
small = ImageFont.truetype(str(FONT), 28 * S)

x = 96 * S
d.text((x, 150 * S), "Walk, Talk, Fork.", font=title, fill=INK)
d.text((x, 330 * S), "歩いて、話して、分かれ道を選ぶ3時間", font=sub, fill=INK)

# 分かれ道の線：1本の道が途中で2つに分かれる
y0, split, end = 450 * S, 560 * S, 1104 * S
w = 3 * S
d.line([(x, y0), (split, y0)], fill=GREEN, width=w)
def curve(dy, dashed=False):
    pts = []
    for i in range(61):
        t = i / 60
        px = split + (end - split) * t
        k = min(t / 0.35, 1)
        py = y0 + dy * (3 * k * k - 2 * k * k * k)
        pts.append((px, py))
    if dashed:
        for i in range(0, len(pts) - 1, 2):
            d.line([pts[i], pts[i + 1]], fill=GREEN, width=w)
    else:
        d.line(pts, fill=GREEN, width=w, joint="curve")
curve(-40 * S)
curve(40 * S, dashed=True)
r = 8 * S
d.ellipse([split - r, y0 - r, split + r, y0 + r], fill=GREEN)

d.text((x, 540 * S), "黒田悠介との対話セッション　3時間・50,000円", font=small, fill=SOFT)

img.resize((W, H), Image.LANCZOS).save(ROOT / "assets/ogp.png", optimize=True)
print("wrote assets/ogp.png")
