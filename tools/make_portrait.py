"""TOPの写真（assets/walk.jpg、2000×1125）から、スマホ用の縦長の写真（assets/walk-portrait.jpg、720×1125）を切り出す。

index.html の <picture> で、画面幅 639px 以下のときだけこの写真を出す（2026-11-15 2回目の見本 t3 の案1）。
左の空いた土の道に名前と予約ボタンが乗り、右に歩く人の足が入るところを切り出す（写るのは1人）。
写真を差し替えたら、切り出す位置（LEFT）を見直してから実行し、続けて tools/make_avif.py で AVIF も作り直す。

使い方（Pillow が入った Python で）:
  python tools/make_portrait.py
  python tools/make_avif.py
"""
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "assets" / "walk.jpg"
DST = ROOT / "assets" / "walk-portrait.jpg"
LEFT, WIDTH = 450, 720   # 元の写真の左から450pxの位置から、幅720px・高さはそのまま

im = Image.open(SRC)
kw = {"icc_profile": im.info["icc_profile"]} if im.info.get("icc_profile") else {}
crop = im.convert("RGB").crop((LEFT, 0, LEFT + WIDTH, im.height))
crop.save(DST, quality=80, optimize=True, progressive=True, **kw)
print(f"{DST.name}: {crop.width}×{crop.height}, {DST.stat().st_size:,} バイト")
