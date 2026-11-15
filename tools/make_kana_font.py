"""明朝の見出しの字詰め（palt）に使う、Shippori Mincho のかなと約物だけのフォント（assets/fonts/shippori-kana.woff2）を作る。

Google Fonts で配られている Shippori Mincho からは、横書きの字詰めに使う palt が削られている。
元のフォント（tools/fonts/ShipporiMincho-Medium.ttf）には palt があるので、かな・約物・全角の記号だけを切り出してサイトに置く。
漢字はこれまでどおり Google Fonts から読み込む。かなと約物の数は決まっているので、文章を直しても作り直す必要はない。
ライセンスは SIL Open Font License 1.1。assets/fonts/OFL.txt を一緒に置き、フォントの中の著作権とライセンスの表記も残す。

元の palt には、「ぜ」「で」「が」「バ」など30字に、送り幅を広げる値（XAdvance が正）が入っている。
そのままだと、詰めたはずの見出しで、その字の後ろにだけすき間ができる（36pxで ぜ 37.8px、で 39.2px など）。
切り出したあとで clamp_palt() を呼び、この30字だけ送り幅を 1em ちょうどにする（2026-11-15 改善の見本 f2）。

使い方（fontTools と brotli が入った Python で）:
  python tools/make_kana_font.py
"""
from pathlib import Path

from fontTools import subset
from fontTools.otlLib.builder import buildSinglePos
from fontTools.pens.boundsPen import BoundsPen
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables import otTables

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "tools/fonts/ShipporiMincho-Medium.ttf"
DST = ROOT / "assets/fonts/shippori-kana.woff2"

# 切り出す範囲：― ‥ …、CJKの記号と約物、ひらがな、カタカナ、全角の記号（英数字は除く）
RANGES = [(0x2015, 0x2015), (0x2025, 0x2026), (0x3000, 0x303F), (0x3041, 0x309F), (0x30A0, 0x30FF)]
FULLWIDTH = "！＃＄％＆（）＊＋，－．／：；＝？［＼］｛｝～"


def palt_lookups(font):
    gpos = font["GPOS"].table
    idx = set()
    for fr in gpos.FeatureList.FeatureRecord:
        if fr.FeatureTag == "palt":
            idx.update(fr.Feature.LookupListIndex)
    return [gpos.LookupList.Lookup[i] for i in sorted(idx)]


def clamp_palt(font, verbose=True):
    """palt で送り幅が 1em を超える字（XAdvance > 0）を、送り幅 1em ちょうどに収める。直した字の数を返す。

    字の左右の空きは元の palt と同じ比率のまま縮め（XPlacement を直す）、1em の中で元と同じ位置関係に置く。
    ほかの字の値は変えない。
    """
    upem = font["head"].unitsPerEm
    hmtx = font["hmtx"]
    glyphset = font.getGlyphSet()
    rev = {g: cp for cp, g in font.getBestCmap().items()}
    changed = 0
    for lookup in palt_lookups(font):
        if lookup.LookupType != 1:
            continue
        # GPOS では、同じ字を含む subtable が複数あっても最初のものだけが効く
        values = {}
        for st in lookup.SubTable:
            for i, g in enumerate(st.Coverage.glyphs):
                if g in values:
                    continue
                v = st.Value if st.Format == 1 else st.Value[i]
                values[g] = (getattr(v, "XPlacement", 0) or 0, getattr(v, "XAdvance", 0) or 0)
        new = {}
        for g, (xp, xa) in values.items():
            adv = hmtx[g][0]
            if adv + xa <= upem:
                new[g] = (xp, xa)
                continue
            pen = BoundsPen(glyphset)
            glyphset[g].draw(pen)
            x_min, _, x_max, _ = pen.bounds
            ink = x_max - x_min
            left = x_min + xp                      # palt をかけたときの左の空き
            right = adv + xa - (x_max + xp)        # 右の空き
            room = max(0, upem - ink)              # 1em に収めたときに残る空き
            new_left = room * left / (left + right) if left + right > 0 else room / 2
            nxp = round(new_left - x_min)
            nxa = upem - adv
            new[g] = (nxp, nxa)
            changed += 1
            if verbose:
                ch = chr(rev[g]) if g in rev else g
                print(f"  {ch} {g}: 送り幅 {adv + xa} → {adv + nxa}  XPlacement {xp:+d} → {nxp:+d}  XAdvance {xa:+d} → {nxa:+d}")
        mapping = {}
        for g, (xp, xa) in new.items():
            vr = otTables.ValueRecord()
            vr.XPlacement = xp
            vr.XAdvance = xa
            mapping[g] = vr
        lookup.SubTable = buildSinglePos(mapping, font.getReverseGlyphMap())
        lookup.SubTableCount = len(lookup.SubTable)
    return changed


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


def main():
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
    n = clamp_palt(font)
    DST.parent.mkdir(parents=True, exist_ok=True)
    font.flavor = "woff2"
    font.save(DST)

    print(f"{DST.relative_to(ROOT)}: {len(codes)} 字, {DST.stat().st_size:,} バイト（palt を {n} 字直した）")
    print("style.css の @font-face の unicode-range:")
    print(ranges(codes))


if __name__ == "__main__":
    main()
