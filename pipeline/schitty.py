#!/usr/bin/env python3
"""schittymd karusell: 7 svarte slides, hvit tekst, emoji-overskrifter. 1080x1350."""
import re, sys, json
from PIL import Image, ImageDraw, ImageFont
W, H = 1080, 1350
BG, FG = (0, 0, 0), (255, 255, 255)
# Stil (Martin 25. nov): «journal» = legeerklæring på kremhvitt notatpapir. «black» = gammel svart stil.
STYLE = "journal"
PAPER, NAVY, RED, MUTED = (247, 242, 232), (28, 40, 92), (200, 40, 52), (90, 100, 140)
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
    items = []
    for word, w in runs(text):
        w = force or w
        # for lange bindestrek-ord deles etter hver bindestrek, så de kan brytes over flere linjer
        if force and seg_width(d, word, F(w, size)) > maxw and "-" in word:
            items += [(pc, w) for pc in re.split(r"(?<=-)", word) if pc]
        else:
            items.append((word, w))
    for word, w in items:
        ww = seg_width(d, word, F(w, size)) + (0 if word.endswith("-") else d.textlength(" ", font=F(w, size)))
        if x and x + ww > maxw:
            lines.append(line); line, x = [], 0
        line.append((word, w, x)); x += ww
    if line: lines.append(line)
    return lines
def journal_bg(lines=True, page=None):
    img = Image.new("RGB", (W, H), PAPER); d = ImageDraw.Draw(img)
    if lines:
        for y in range(300, H - 90, 64): d.line((70, y, W - 70, y), fill=(206, 219, 236), width=2)
        d.line((112, 230, 112, H - 70), fill=(232, 160, 160), width=3)
    d.text((70, 62), "Dr. Schitty", font=F("Bold", 44), fill=NAVY)
    d.text((70, 118), "Legekontor for hverdagsplager · Ingen timebestilling", font=F("Medium", 27), fill=MUTED)
    d.line((70, 172, W - 70, 172), fill=RED, width=5)
    foot = "@schittymd" + (f"   ·   side {page} av 7" if page else "")
    d.text((W - 70 - d.textlength(foot, font=F("Medium", 26)), H - 62), foot, font=F("Medium", 26), fill=MUTED)
    return img
def stamp(img, text, xy, angle=-12, size=58):
    f = F("Bold", size); tw = ImageDraw.Draw(img).textlength(text, font=f)
    st = Image.new("RGBA", (int(tw) + 70, size + 60), (0, 0, 0, 0)); sd = ImageDraw.Draw(st)
    sd.rounded_rectangle((4, 4, st.width - 4, st.height - 4), radius=14, outline=RED + (225,), width=7)
    sd.text((35, 20), text, font=f, fill=RED + (225,))
    st = st.rotate(angle, expand=True, resample=Image.BICUBIC); img.paste(st, xy, st)
def cover_journal(post):
    """Forside i journal-stil: LEGEERKLÆRING, forkortelse stort, fullt navn, ICD, stempel."""
    global FG
    img = journal_bg(lines=False); d = ImageDraw.Draw(img)
    abbr, _, full = post["navn"].partition(" – ")
    if not full: abbr, full = post["navn"], ""
    d.text((86, 300), "LEGEERKLÆRING", font=F("Bold", 36), fill=RED)
    e = emoji_img("🩺", 112); img.paste(e, (86, 380), e)
    asz = 150
    while asz > 70 and d.textlength(abbr, font=F("Black", asz)) > W - 172 - 140: asz -= 6
    d.text((86 + 140, 372 + (150 - asz) // 2), abbr, font=F("Black", asz), fill=NAVY)
    y = 560
    if full:
        hs = 72
        pieces = [pc for pc in re.split(r"(?<=-)| ", full) if pc]
        while hs > 40 and max(seg_width(d, pc, F("Bold", hs)) for pc in pieces) > W - 172: hs -= 2
        FG = NAVY
        for ln in wrap(d, full, hs, W - 172, force="Bold"):
            for word, w, x in ln: draw_word(img, d, (86 + x, y), word, F("Bold", hs))
            y += int(hs * 1.22)
    d.text((86, y + 40), "ICD-kode: " + post["icd"], font=F("Medium", 34), fill=MUTED)
    d.line((86, 1150, 560, 1150), fill=NAVY, width=3)
    FG = NAVY; draw_word(img, d, (86, 1166), "Pasient:", F("Medium", 36)); draw_word(img, d, (86 + d.textlength("Pasient: ", font=F("Medium", 36)), 1166), "deg", F("Bold", 36))
    draw_word(img, d, (86 + d.textlength("Pasient: deg ", font=F("Medium", 36)), 1166), "👇", F("Medium", 36))
    stamp(img, "DIAGNOSTISERT", (455, 985))
    return img
def slide(head, emoji, body, bullets=False, title=False, size=None, page=None):
    global FG
    journal = STYLE == "journal"
    if journal:
        img = journal_bg(page=page); FG = NAVY
    else:
        img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    x0, maxw = (150, W - 150 - 80) if journal else (86, W - 172)
    size = size or (64 if title else 50)
    lh = int(size * 1.32)
    blocks = []
    hs0 = 64 if title else 56
    if head:
        # krymp overskriften til det lengste ordet (f.eks. lange bindestrek-navn) får plass
        hw = maxw - (84 if emoji else 0)
        pieces = [pc for wd, _ in runs(head) for pc in re.split(r"(?<=-)", wd) if pc]
        while hs0 > 36 and max(seg_width(d, pc, F("Bold", hs0)) for pc in pieces) > hw:
            hs0 -= 2
        blocks.append(("head", wrap(d, head, hs0, hw, force="Bold")))
    items = body if isinstance(body, list) else [body]
    for it in items:
        blocks.append(("item", wrap(d, it, size, maxw - (44 if bullets else 0))))
    total = sum(len(l) * (int(hs0 * 1.3) if k == "head" else lh) + (40 if k == "head" else 30) for k, l in blocks)
    avail = (H - 230 - 110) if journal else (H - 180)
    if total > avail and size > 34:
        return slide(head, emoji, body, bullets, title, size - 4, page)
    y = (230 + (H - 110 - total)) // 2 if journal else (H - total) // 2
    if journal: y = max(250, y)
    for kind, lines in blocks:
        if kind == "head":
            hs = hs0
            if emoji:
                e = emoji_img(emoji, int(hs * 1.05)); img.paste(e, (x0, y + 6), e)
            if journal: FG = RED
            for ln in lines:
                for word, w, x in ln:
                    draw_word(img, d, (x0 + (84 if emoji else 0) + x, y), word, F("Bold", hs))
                y += int(hs * 1.3)
            if journal: FG = NAVY
            y += 40
        else:
            if bullets:
                if journal: d.ellipse((x0 + 4, y + size * 0.42, x0 + 20, y + size * 0.42 + 16), fill=RED)
                else: d.text((x0, y), "•", font=F("Medium", size), fill=FG)
            for ln in lines:
                for word, w, x in ln:
                    draw_word(img, d, (x0 + (44 if bullets else 0) + x, y), word, F(w, size))
                y += lh
            y += 30
    return img
def render(post, prefix):
    first = cover_journal(post) if STYLE == "journal" else slide(post["navn"], "🩺", [], title=True)
    s = [first,
         slide(None, None, [f"**ICD-kode:** {post['icd']}", f"**Rammer:** {post['rammer']}"], page=2),
         slide("Definisjon:", "🔍", post["definisjon"], page=3),
         slide("Symptomer:", "⚠️", post["symptomer"], bullets=True, page=4),
         slide("Årsaker:", "🧬", post["arsaker"], bullets=True, page=5),
         slide("Diagnostiske kriterier:", "🔬", post["kriterier"], bullets=True, page=6),
         slide("Behandling:", "💊", post["behandling"], bullets=True, page=7)]
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
