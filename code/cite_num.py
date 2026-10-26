# -*- coding: utf-8 -*-
"""Convert author-year citations to numbered [n] citations in order of first appearance."""
import re


def _narr(key):
    """'Weatherhead et al., 1998' -> 'Weatherhead et al. (1998)'"""
    a, y = key.rsplit(", ", 1)
    return f"{a} ({y})", a


def number(blocks, refs):
    keys = [k for k, _ in refs]
    order = []

    def idx(k):
        if k not in order:
            order.append(k)
        return order.index(k) + 1

    paren = re.compile(r"\(([^()]*?\d{4}[a-z]?)\)")
    out = []
    for kind, txt in blocks:
        if kind not in ("p", "bul"):
            out.append((kind, txt)); continue
        # walk through the text so that numbering follows reading order
        pieces = []
        pos = 0
        pat = re.compile("|".join([re.escape(_narr(k)[0]) for k in keys] + [paren.pattern]))
        for m in pat.finditer(txt):
            s = m.group(0)
            rep = None
            for k in keys:
                if s == _narr(k)[0]:
                    rep = f"{_narr(k)[1]} [{idx(k)}]"
                    break
            if rep is None:
                parts = [x.strip() for x in m.group(1).split(";")]
                if all(p in keys for p in parts):
                    nums = sorted(idx(p) for p in parts)
                    rep = "[" + ",".join(map(str, nums)) + "]"
                    if txt[m.start() - 1:m.start()] == " ":
                        pass
            if rep is None:
                continue
            pieces.append(txt[pos:m.start()]); pieces.append(rep); pos = m.end()
        pieces.append(txt[pos:])
        out.append((kind, "".join(pieces)))
    unused = [k for k in keys if k not in order]
    ref_map = dict(refs)
    numbered = [(i + 1, ref_map[k]) for i, k in enumerate(order)]
    leftover = [s for b in out if b[0] in ("p", "bul") for s in re.findall(r"\([A-Z][^()]*?\d{4}\)", b[1])]
    return out, numbered, unused, leftover
