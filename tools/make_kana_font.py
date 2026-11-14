"""明朝の見出しの字詰め（palt）に使う、Shippori Mincho のかなと約物だけのフォント（assets/fonts/shippori-kana.woff2）を作る。

Google Fonts で配られている Shippori Mincho からは、横書きの字詰めに使う palt が削られている。
元のフォント（tools/fonts/ShipporiMincho-Medium.ttf）には palt があるので、かな・約物・全角の記号だけを切り出してサイトに置く。
漢字はこれまでどおり Google Fonts から読み込む。かなと約物の数は決まっているので、文章を直しても作り直す必要はない。
ライセンスは SIL Open Font License 1.1。assets/fonts/OFL.txt を一緒に置き、フォントの中の著作権とライセンスの表記も残す。

使い方（fontTools と brotli が入った Python で）:
  python tools/make_kana_font.py
"""
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "tools/fonts/ShipporiMincho-Medium.ttf"
DST = ROOT / "assets/fonts/shippori-kana.woff2"

# 切り出す範囲：― ‥ …、CJKの記号と約物、ひらがな、カタカナ、全角の記号（英数字は除く）
RANGES = [(0x2015, 0x2015), (0x2025, 0x2026), (0x3000, 0x303F), (0x3041, 0x309F), (0x30A0, 0x30FF)]
FULLWIDTH = "！＃＄％＆（）＊＋，－．／：；＝？［＼］｛｝～"

font = TTFont(SRC)
cmap = font.getBestCmap()
codes = sorted(cp for cp in cmap if any(a <= cp <= b for a, b in RANGES) or chr(cp) in FULLWIDTH)

opts = subset.Options()
opts.flavor = "woff2"
opts.layout_features = ["palt"]  # 横書きの字詰めだけ使う
opts.name_IDs = [0, 1, 2, 3, 4, 5, 6, 13, 14]  # 著作権とライセンスの表記を残す
sub = subset.Subsetter(opts)
sub.populate(unicodes=codes)
sub.subset(font)
DST.parent.mkdir(parents=True, exist_ok=True)
font.flavor = "woff2"
font.save(DST)


def ranges(cps):
    out, start, prev = [], cps[0], cps[0]
    for cp in cps[1:] + [None]:
        if cp is not None and cp == prev + 1:
            prev = cp
            continue
        out.append(f"U+{start:04X}" if start == prev else f"U+{start:04X}-{prev:04X}")
        if cp is not None:
            start = prev = cp
    return ", ".join(out)


print(f"{DST.relative_to(ROOT)}: {len(codes)} 字, {DST.stat().st_size:,} バイト")
print("style.css の @font-face の unicode-range:")
print(ranges(codes))
