"""ホーム画面のアイコン（assets/apple-touch-icon.png、180×180px）を、ファビコン（assets/favicon.svg）と同じ絵で作る（2026-11-15 見本 b3）。
深い緑の地に、生成りの分かれ道の線。iPhone・iPad が角を丸めるので、地は角を丸めずに四角いっぱいに塗る（透明にすると黒く塗られる）。
線の形は favicon.svg の path（32×32 の枠で M5 16h8c4 0 5-6 9-6h5 と M13 16c4 0 5 6 9 6h5、太さ2.4、端は丸）をそのまま写す。
favicon.svg の絵を変えたら、ここの PATHS も合わせて作り直す。
使い方（Pillow が入った Python で）: python -I tools/make_touch_icon.py
"""
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets/apple-touch-icon.png"
SIZE, SS = 180, 8                 # 8倍の大きさで描いてから縮め、線の縁をなめらかにする
GREEN, PAPER = "#2F5D4A", "#F4F0E6"
STROKE = 2.4

# favicon.svg の2本の線。("L", 終点) は直線、("C", 制御点1, 制御点2, 終点) は3次ベジェ（32×32 の座標）
PATHS = [
    [(5, 16), ("L", (13, 16)), ("C", (17, 16), (18, 10), (22, 10)), ("L", (27, 10))],
    [(13, 16), ("C", (17, 16), (18, 22), (22, 22)), ("L", (27, 22))],
]


def points(path, steps=48):
    pts = [path[0]]
    for seg in path[1:]:
        p0 = pts[-1]
        if seg[0] == "L":
            pts.append(seg[1])
        else:
            _, c1, c2, p3 = seg
            for i in range(1, steps + 1):
                t = i / steps
                u = 1 - t
                pts.append(tuple(u ** 3 * p0[k] + 3 * u * u * t * c1[k] + 3 * u * t * t * c2[k] + t ** 3 * p3[k] for k in range(2)))
    return pts


def main():
    big = SIZE * SS
    k = big / 32
    img = Image.new("RGB", (big, big), GREEN)
    d = ImageDraw.Draw(img)
    w = STROKE * k
    for path in PATHS:
        # 線の上に、太さと同じ直径の丸を細かく並べて押していく（折れ目に欠けが出ず、端も丸くなる）
        pts = [(x * k, y * k) for x, y in points(path)]
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            n = max(1, int(((x1 - x0) ** 2 + (y1 - y0) ** 2) ** .5 / 2))
            for i in range(n + 1):
                x, y = x0 + (x1 - x0) * i / n, y0 + (y1 - y0) * i / n
                d.ellipse((x - w / 2, y - w / 2, x + w / 2, y + w / 2), fill=PAPER)
    img.resize((SIZE, SIZE), Image.LANCZOS).save(OUT, optimize=True)
    print("wrote", OUT.relative_to(ROOT), OUT.stat().st_size, "bytes")


if __name__ == "__main__":
    main()
