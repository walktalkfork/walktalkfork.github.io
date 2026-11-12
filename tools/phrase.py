"""HTMLの本文に、BudouX で文節の切れ目ごとに <wbr> を入れる。

CSS の word-break: keep-all と組み合わせて、語の途中で改行しないようにする。
何度実行しても同じ結果になるよう、最初に既存の <wbr> を外してから入れ直す。

使い方（budoux が入った Python で）:
  python tools/phrase.py index.html tokushoho.html cancel.html privacy.html
"""
import html
import re
import sys

import budoux

parser = budoux.load_default_japanese_parser()
SKIP = re.compile(r"(<(script|style|svg|title)\b.*?</\2>)", re.S | re.I)
TAG = re.compile(r"(<[^>]+>)")
JA = re.compile(r"[぀-ヿ㐀-鿿]")


# BudouX が語の途中で区切ってしまう語。ここに足すと、その語の中では改行しない
KEEP = ["方向", "方法"]


def crosses(prev, nxt, word):
    """prev と nxt の境目が word の途中に当たるか。"""
    both = prev + nxt
    i = both.find(word)
    while i != -1:
        if i < len(prev) < i + len(word):
            return True
        i = both.find(word, i + 1)
    return False


def merge_keep(parts):
    """KEEP の語をまたぐ区切りを外す。"""
    out = []
    for p in parts:
        if out and any(crosses(out[-1], p, w) for w in KEEP):
            out[-1] += p
        else:
            out.append(p)
    return out


def phrase_text(text):
    if not JA.search(text):
        return text
    raw = html.unescape(text)
    parts = merge_keep(parser.parse(raw))
    return "<wbr>".join(html.escape(p, quote=False) for p in parts)


def process(src):
    src = src.replace("<wbr>", "")
    head, sep, body = src.partition("<body>")
    if not sep:
        return src
    out = []
    for chunk in SKIP.split(body):
        if chunk is None:
            continue
        if SKIP.fullmatch(chunk) or chunk.lower() in ("script", "style", "svg", "title"):
            out.append(chunk if SKIP.fullmatch(chunk) else "")
            continue
        out.append("".join(p if p.startswith("<") else phrase_text(p) for p in TAG.split(chunk)))
    return head + sep + "".join(out)


for path in sys.argv[1:]:
    with open(path, encoding="utf-8") as f:
        s = f.read()
    with open(path, "w", encoding="utf-8") as f:
        f.write(process(s))
    print("phrased", path)
