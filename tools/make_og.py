"""共有画像（assets/ogp.png、1200×630）を作る。TOPと同じ歩く写真に、名前とサブタイトルを重ねる。

書体は tools/fonts/ShipporiMincho-Medium.ttf（Google Fonts、OFL）。なければ
https://github.com/google/fonts/raw/main/ofl/shipporimincho/ShipporiMincho-Medium.ttf から取ってくる。
使い方（Pillow が入った Python で）: python tools/make_og.py
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
FONT = ROOT / "tools/fonts/ShipporiMincho-Medium.ttf"
PHOTO = ROOT / "assets/walk.jpg"
W, H = 1200, 630

photo = Image.open(PHOTO).convert("RGB")
# 写真を 1200×630 に切り抜く（横は右寄り、縦は下寄りで足もとを残す）
scale = max(W / photo.width, H / photo.height)
photo = photo.resize((round(photo.width * scale), round(photo.height * scale)), Image.LANCZOS)
x0 = int((photo.width - W) * 0.62)
y0 = int((photo.height - H) * 0.6)
img = photo.crop((x0, y0, x0 + W, y0 + H))

# 左側を少し暗くして文字を読みやすくする（サイトのTOPと同じ考え方）
shade = Image.new("L", (W, 1))
for x in range(W):
    t = x / W
    a = 0.48 if t < 0.0 else max(0.0, 0.48 - 0.48 * (t / 0.75))
    shade.putpixel((x, 0), int(255 * a))
shade = shade.resize((W, H))
img = Image.composite(Image.new("RGB", (W, H), (22, 20, 16)), img, shade)

d = ImageDraw.Draw(img)
title = ImageFont.truetype(str(FONT), 104)
sub = ImageFont.truetype(str(FONT), 38)
d.text((72, 360), "Walk, Talk, Fork.", font=title, fill="#FFFDF8")
d.text((76, 500), "歩いて、話して、分かれ道を選ぶ3時間", font=sub, fill="#FFFDF8")
img.save(ROOT / "assets/ogp.png", optimize=True)
print("wrote assets/ogp.png")
