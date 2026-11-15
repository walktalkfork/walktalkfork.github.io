"""プロフィールの写真（assets/kuroda.jpg、799×1000）から、ファーストビューの下に出す顔の丸の画像
（assets/kuroda-face.jpg、104×104。画面では52pxの丸に2倍の解像度で出す）を切り出す。

index.html の .hero-guide（「一緒に歩くのは、キャリア研究家の黒田悠介です」。2026-11-15 2回目の見本 c1 の「顔あり」）で使う。
写真を差し替えたら、切り出す位置（BOX）を見直してから実行し、続けて tools/make_avif.py で AVIF も作り直す。

使い方（Pillow が入った Python で）:
  python tools/make_face.py
  python tools/make_avif.py
"""
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "assets" / "kuroda.jpg"
DST = ROOT / "assets" / "kuroda-face.jpg"
BOX = (230, 190, 570, 530)   # 顔のまわりの正方形（左・上・右・下。見本 c1 で丸に見せていた範囲）
SIZE = 104

im = Image.open(SRC)
kw = {"icc_profile": im.info["icc_profile"]} if im.info.get("icc_profile") else {}
face = im.convert("RGB").crop(BOX).resize((SIZE, SIZE), Image.LANCZOS)
face.save(DST, quality=82, optimize=True, progressive=True, **kw)
print(f"{DST.name}: {face.width}×{face.height}, {DST.stat().st_size:,} バイト")
