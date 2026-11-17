#!/usr/bin/env python3
"""schittymd karusell: 7 svarte slides, hvit tekst, emoji-overskrifter. 1080x1350."""
import re, sys, json
from PIL import Image, ImageDraw, ImageFont
W, H = 1080, 1350
BG, FG = (0, 0, 0), (255, 255, 255)
INTER = "/usr/share/fonts/opentype/inter/Inter-%s.otf"
EMOJI = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
_f = {}
def F(w, s):
    if (w, s) not in _f: _f[(w, s)] = ImageFont.truetype(INTER % w, s)
    return _f[(w, s)]
_em = ImageFont.truetype(EMOJI, 109)
def emoji_img(ch, size):
    im = Image.new("RGBA", (136, 128), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((0, 0), ch, font=_em, embedded_color=True)
    im = im.crop(im.getbbox())
    return im.resize((size, int(size * im.height / im.width)), Image.LANCZOS)
EMO = re.compile("((?:[\U0001F000-\U0001FAFF\u2600-\u27BF\u2B00-\u2BFF\u2300-\u23FF]\uFE0F?(?:\u200D[\U0001F000-\U0001FAFF\u2600-\u27BF]\uFE0F?)*)+)")
_ecache = {}
def emoji_seq(seq, size):
    key = (seq, size)
    if key not in _ecache:
        parts = []
        for ch in re.findall("[^\uFE0F\u200D](?:\uFE0F)?(?:\u200D[^\uFE0F\u200D]\uFE0F?)*", seq):
            im = Image.new("RGBA", (400, 160), (0, 0, 0, 0))
            ImageDraw.Draw(im).text((0, 0), ch, font=_em, embedded_color=True)
            bb = im.getbbox()
            if bb: parts.append(im.crop(bb).resize((size, size), Image.LANCZOS))
        w = len(parts) * int(size * 1.08)
        out = Image.new("RGBA", (max(w, 1), size), (0, 0, 0, 0))
        for i, p in enumerate(parts): out.paste(p, (i * int(size * 1.08), 0), p)
        _ecache[key] = out
    return _ecache[key]
def seg_width(d, word, font):
    w = 0
    for part in EMO.split(word):
        if not part: continue
        w += emoji_seq(part, int(font.size * 0.92)).width if EMO.fullmatch(part) else d.textlength(part, font=font)
    return w
def draw_word(img, d, xy, word, font):
    x, y = xy
    for part in EMO.split(word):
        if not part: continue
        if EMO.fullmatch(part):
            e = emoji_seq(part, int(font.size * 0.92)); img.paste(e, (int(x), int(y + font.size * 0.12)), e); x += e.width
        else:
            d.text((x, y), part, font=font, fill=FG); x += d.textlength(part, font=font)
def runs(text):
    """**fet** og _kursiv_ -> [(ord, vekt)]"""
    out = []
    for part in re.split(r"(\*\*.+?\*\*|_.+?_)", text):
        if not part: continue
        w = "Bold" if part.startswith("**") else ("MediumItalic" if part.startswith("_") else "Medium")
        part = part.strip("*") if w == "Bold" else (part[1:-1] if w == "MediumItalic" else part)
        for word in part.split(" "):
            if word: out.append((word, w))
    return out
def wrap(d, text, size, maxw, force=None):
    lines, line, x = [], [], 0
    for word, w in runs(text):
        w = force or w
        ww = seg_width(d, word, F(w, size)) + d.textlength(" ", font=F(w, size))
        if x and x + ww > maxw:
            lines.append(line); line, x = [], 0
        line.append((word, w, x)); x += ww
    if line: lines.append(line)
    return lines
def slide(head, emoji, body, bullets=False, title=False, size=None):
    img = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(img)
    x0, maxw = 86, W - 172
    size = size or (64 if title else 50)
    lh = int(size * 1.32)
    blocks = []
    if head:
        blocks.append(("head", wrap(d, head, 56 if not title else 64, maxw - (84 if emoji else 0), force="Bold")))
    items = body if isinstance(body, list) else [body]
    for it in items:
        blocks.append(("item", wrap(d, it, size, maxw - (44 if bullets else 0))))
    hs0 = 64 if title else 56
    total = sum(len(l) * (int(hs0 * 1.3) if k == "head" else lh) + (40 if k == "head" else 30) for k, l in blocks)
    if total > H - 180 and size > 34:
        return slide(head, emoji, body, bullets, title, size - 4)
    y = (H - total) // 2
    for kind, lines in blocks:
        if kind == "head":
            hs = 64 if title else 56
            if emoji:
                e = emoji_img(emoji, int(hs * 1.05)); img.paste(e, (x0, y + 6), e)
            for ln in lines:
                for word, w, x in ln:
                    draw_word(img, d, (x0 + (84 if emoji else 0) + x, y), word, F("Bold", hs))
                y += int(hs * 1.3)
            y += 40
        else:
            if bullets:
                d.text((x0, y), "•", font=F("Medium", size), fill=FG)
            for ln in lines:
                for word, w, x in ln:
                    draw_word(img, d, (x0 + (44 if bullets else 0) + x, y), word, F(w, size))
                y += lh
            y += 30
    return img
def render(post, prefix):
    s = [slide(post["navn"], "🩺", [], title=True),
         slide(None, None, [f"**ICD-kode:** {post['icd']}", f"**Rammer:** {post['rammer']}"]),
         slide("Definisjon:", "🔍", post["definisjon"]),
         slide("Symptomer:", "⚠️", post["symptomer"], bullets=True),
         slide("Årsaker:", "🧬", post["arsaker"], bullets=True),
         slide("Diagnostiske kriterier:", "🔬", post["kriterier"], bullets=True),
         slide("Behandling:", "💊", post["behandling"], bullets=True)]
    for i, im in enumerate(s, 1): im.save(f"{prefix}_{i}.png")
    return s
def load(path):
    return {p["id"]: p for p in (json.loads(l) for l in open(path, encoding="utf-8") if l.strip())}

def sheet(slides, out):
    sh = Image.new("RGB", (4 * 360 + 50, 2 * 450 + 30), (40, 40, 40))
    for i, im in enumerate(slides):
        sh.paste(im.resize((360, 450)), (10 + (i % 4) * 370, 10 + (i // 4) * 460))
    sh.save(out)

if __name__ == "__main__":
    # schitty.py render BANK.jsonl IDS OUTDIR   -> OUTDIR/schittymd_NNN_1..7.png + oversikt
    import os
    _, cmd, bank, ids, outdir = sys.argv
    posts = load(bank); os.makedirs(outdir, exist_ok=True)
    for i in ids.split(","):
        sl = render(posts[i], os.path.join(outdir, f"schittymd_{i}"))
        sheet(sl, os.path.join(outdir, f"oversikt_{i}.png"))
        print(i, "ok")
