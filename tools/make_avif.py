"""index.html の写真と絵（assets/*.jpg）から、軽い AVIF（assets/*.avif）を作る。

index.html では <picture> の <source type="image/avif"> でこの AVIF を出し、
AVIF に対応しないブラウザには今の JPEG を出す。JPEG を差し替えたら、もう一度実行する。
画質は 65（拡大すると地面の小石や絵のざらつきが少しなめらかになるが、画面に出る大きさでは見分けがつかない）。

使い方（AVIF に対応した Pillow 11 以降が入った Python で）:
  python tools/make_avif.py
"""
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
NAMES = ["walk.jpg", "walk-1000.jpg", "route-jimbocho.jpg", "route-marunouchi.jpg", "kuroda.jpg"]
QUALITY = 65

for name in NAMES:
    src = ASSETS / name
    dst = src.with_suffix(".avif")
    im = Image.open(src)
    kw = {"icc_profile": im.info["icc_profile"]} if im.info.get("icc_profile") else {}
    im.save(dst, "AVIF", quality=QUALITY, speed=4, **kw)
    print(f"{dst.name}: {src.stat().st_size:,} → {dst.stat().st_size:,} バイト")
