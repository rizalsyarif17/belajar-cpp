"""Graphic elements + easing for the compositor. All drawing in RGBA at 1080x1920."""
import math, functools, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

W, H = 1080, 1920
FONTS = '/tmp/claude-0/-home-user-belajar-cpp/d18ffba8-f99d-5d8b-bae5-b4e8fcb70ea2/scratchpad/assets/fonts/'
CAP_FONT = FONTS + 'Montserrat-ExtraBold.ttf'
STICK_FONT = FONTS + 'Montserrat-BlackItalic.ttf'
TITLE_FONT = FONTS + 'Anton.ttf'
EMOJI_FONT = '/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf'

PURPLE = (121, 11, 193, 255)   # sampled from reference highlight box

# ---------------- easing ----------------
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease_out_cubic(x): x = clamp(x); return 1 - (1 - x) ** 3
def ease_in_cubic(x): x = clamp(x); return x ** 3
def ease_in_out_cubic(x):
    x = clamp(x); return 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2
def ease_out_back(x, s=1.70158):
    x = clamp(x); c3 = s + 1; return 1 + c3 * (x - 1) ** 3 + s * (x - 1) ** 2
def ease_out_quint(x): x = clamp(x); return 1 - (1 - x) ** 5

@functools.lru_cache(None)
def font(path, size): return ImageFont.truetype(path, size)

def paste_scaled(canvas, sprite, cx, cy, scale=1.0, rot=0.0, alpha=1.0):
    """Alpha-composite sprite centred at (cx,cy) with scale/rotation/opacity."""
    if scale <= 0.01 or alpha <= 0.01: return
    sp = sprite
    if abs(scale - 1) > 1e-3:
        sp = sp.resize((max(1, int(sp.width * scale)), max(1, int(sp.height * scale))), Image.BILINEAR)
    if abs(rot) > 0.05:
        sp = sp.rotate(rot, resample=Image.BICUBIC, expand=True)
    if alpha < 0.999:
        a = sp.getchannel('A').point(lambda v: int(v * alpha)); sp = sp.copy(); sp.putalpha(a)
    canvas.alpha_composite(sp, (int(cx - sp.width / 2), int(cy - sp.height / 2))) if \
        0 <= int(cx - sp.width / 2) and 0 <= int(cy - sp.height / 2) and int(cx + sp.width / 2) <= W and int(cy + sp.height / 2) <= H \
        else _safe_composite(canvas, sp, int(cx - sp.width / 2), int(cy - sp.height / 2))

def _safe_composite(canvas, sp, x, y):
    x0, y0 = max(0, x), max(0, y); x1, y1 = min(W, x + sp.width), min(H, y + sp.height)
    if x1 <= x0 or y1 <= y0: return
    canvas.alpha_composite(sp.crop((x0 - x, y0 - y, x1 - x, y1 - y)), (x0, y0))

def shadowed_text(text, fnt, fill=(255, 255, 255, 255), stroke=0, stroke_fill=(0, 0, 0, 255),
                  shadow=(3, 4), shadow_alpha=170, blur=1.5, pad=12):
    l, t, r, b = fnt.getbbox(text, stroke_width=stroke)
    w, h = r - l + pad * 2 + abs(shadow[0]), b - t + pad * 2 + abs(shadow[1])
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    if shadow_alpha:
        sh = Image.new('RGBA', (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(sh)
        d.text((pad - l + shadow[0], pad - t + shadow[1]), text, font=fnt, fill=(0, 0, 0, shadow_alpha),
               stroke_width=stroke, stroke_fill=(0, 0, 0, shadow_alpha))
        if blur: sh = sh.filter(ImageFilter.GaussianBlur(blur))
        im.alpha_composite(sh)
    d = ImageDraw.Draw(im)
    d.text((pad - l, pad - t), text, font=fnt, fill=fill, stroke_width=stroke, stroke_fill=stroke_fill)
    return im

# ---------------- captions ----------------
CAP_SIZE = 34          # reference: ~12px cap height at 576w  -> ~22px at 1080w -> 34px font
CAP_Y = 1609           # reference: 83.8% of frame height

@functools.lru_cache(maxsize=512)
def caption_image(words, active):
    """words: tuple of str (uppercase); active: index of highlighted word (-1 none)."""
    fnt = font(CAP_FONT, CAP_SIZE)
    space = int(CAP_SIZE * 0.30)
    padx, pady = 7, 5
    maxw = int(W * 0.62)
    # line wrapping (max 2 lines)
    widths = [fnt.getlength(w) for w in words]
    lines, cur, cw = [], [], 0
    for i, w in enumerate(widths):
        if cur and cw + space + w > maxw: lines.append(cur); cur, cw = [], 0
        cw += (space if cur else 0) + w; cur.append(i)
    if cur: lines.append(cur)
    asc, desc = fnt.getmetrics()
    capb = fnt.getbbox('H'); cap_top, cap_bot = capb[1], capb[3]
    lh = int((cap_bot - cap_top) + pady * 2 + 8)
    imw = maxw + 60; imh = lh * len(lines) + 30
    im = Image.new('RGBA', (imw, imh), (0, 0, 0, 0))
    sh = Image.new('RGBA', (imw, imh), (0, 0, 0, 0))
    box = Image.new('RGBA', (imw, imh), (0, 0, 0, 0))
    dt, ds, db = ImageDraw.Draw(im), ImageDraw.Draw(sh), ImageDraw.Draw(box)
    for li, line in enumerate(lines):
        lw = sum(widths[i] for i in line) + space * (len(line) - 1)
        x = (imw - lw) / 2; y = 15 + li * lh + pady
        for i in line:
            if i == active:
                db.rounded_rectangle((x - padx, y - pady + 1, x + widths[i] + padx, y + (cap_bot - cap_top) + pady + 1),
                                     radius=4, fill=PURPLE)
            ds.text((x + 2, y - cap_top + 3), words[i], font=fnt, fill=(0, 0, 0, 190))
            dt.text((x, y - cap_top), words[i], font=fnt, fill=(255, 255, 255, 255))
            x += widths[i] + space
    sh = sh.filter(ImageFilter.GaussianBlur(1.6))
    out = Image.new('RGBA', (imw, imh), (0, 0, 0, 0))
    out.alpha_composite(sh); out.alpha_composite(box); out.alpha_composite(im)
    return out

def draw_caption(canvas, group, t):
    """group: dict(t0,t1,words=[{text,t0,t1}]); pop-in on group start like reference."""
    ws = tuple(w['text'].upper() for w in group['words'])
    active = -1
    for i, w in enumerate(group['words']):
        if w['t0'] - 0.02 <= t: active = i
    img = caption_image(ws, active)
    k = (t - group['t0']) / 0.13
    s = 0.86 + 0.14 * ease_out_back(k, 2.2) if k < 1 else 1.0
    paste_scaled(canvas, img, W / 2, CAP_Y, s)

# ---------------- pixel hearts overlay ----------------
HEART = ["..XX...XX..",
         ".XXXX.XXXX.",
         "XXXXXXXXXXX",
         "XXXXXXXXXXX",
         "XXXXXXXXXXX",
         ".XXXXXXXXX.",
         "..XXXXXXX..",
         "...XXXXX...",
         "....XXX....",
         ".....X....."]

@functools.lru_cache(None)
def heart_sprite(px):
    gw, gh = len(HEART[0]), len(HEART)
    pad = px * 3
    im = Image.new('RGBA', (gw * px + pad * 2, gh * px + pad * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for y, row in enumerate(HEART):
        for x, c in enumerate(row):
            if c == 'X':
                col = (255, 120, 225, 255)
                if (x, y) in ((2, 1), (3, 1), (1, 2), (2, 2), (1, 3)): col = (255, 225, 250, 255)  # highlight
                d.rectangle((pad + x * px, pad + y * px, pad + (x + 1) * px - 1, pad + (y + 1) * px - 1), fill=col)
    glow = im.filter(ImageFilter.GaussianBlur(px * 1.4))
    ga = glow.getchannel('A').point(lambda v: min(255, int(v * 1.6)))
    g = Image.new('RGBA', im.size, (255, 60, 220, 0)); g.putalpha(ga)
    out = Image.new('RGBA', im.size, (0, 0, 0, 0)); out.alpha_composite(g); out.alpha_composite(im)
    return out

class Hearts:
    def __init__(self, seed=3, n=26):
        r = random.Random(seed)
        self.items = []
        for i in range(n):
            # keep the centre (face) mostly clear: hearts hug the edges / top / bottom
            side = r.random()
            if side < .35: x = r.uniform(-40, 300)
            elif side < .7: x = r.uniform(780, 1120)
            else: x = r.uniform(0, W)
            y = r.uniform(80, H - 80) if side < .7 else r.choice([r.uniform(0, 420), r.uniform(1450, 1900)])
            self.items.append(dict(x=x, y=y, px=r.choice([8, 10, 12, 14, 16]), delay=r.uniform(0, .35),
                                   ph=r.uniform(0, 6.28), sp=r.uniform(25, 70)))
    def draw(self, canvas, t, dur):
        fin = ease_out_cubic(t / .25); fout = 1 - ease_in_cubic((t - (dur - .25)) / .25)
        a = min(fin, fout)
        tint = Image.new('RGBA', (W, H), (255, 70, 200, int(48 * a)))
        canvas.alpha_composite(tint)
        for it in self.items:
            k = (t - it['delay']) / .3
            if k <= 0: continue
            s = ease_out_back(k, 2.5) * (1 + .08 * math.sin(t * 7 + it['ph']))
            y = it['y'] - it['sp'] * t
            paste_scaled(canvas, heart_sprite(it['px']), it['x'], y, s * (0.4 + 0.6 * fout), 0, a)

# ---------------- sad scrolling text rows ----------------
class SadRows:
    PHRASES = ["Huhuhu...  ", "Sedih banget...  ", "Nangis nih...  ", "Hiks hiks...  "]
    def __init__(self, seed=5):
        r = random.Random(seed)
        self.rows = []
        for i, y in enumerate([150, 300, 470, 640, 820, 1000]):
            txt = ''.join(r.sample(self.PHRASES, 4)) * 2
            img = shadowed_text(txt, font(STICK_FONT, r.choice([54, 60, 66])), stroke=5,
                                shadow=(5, 6), shadow_alpha=150, blur=2)
            self.rows.append(dict(img=img, y=y, dir=1 if i % 2 else -1, sp=r.uniform(140, 210), off=r.uniform(0, 400)))
    def draw(self, canvas, t, dur):
        fin = ease_out_cubic(t / .3); a = 1 - ease_in_cubic((t - (dur - .2)) / .2)
        for i, rw in enumerate(self.rows):
            k = ease_out_cubic((t - i * .04) / .35)
            base = -rw['off'] - rw['sp'] * t if rw['dir'] < 0 else -rw['img'].width / 2 + rw['off'] + rw['sp'] * t
            slide = (1 - k) * 700 * rw['dir']
            x = base + slide + rw['img'].width / 2
            paste_scaled(canvas, rw['img'], x, rw['y'], 1.0, 0, a * min(1, k * 1.2))

# ---------------- cartoon tears ----------------
@functools.lru_cache(None)
def tear_stream(h, w=34):
    im = Image.new('RGBA', (w + 16, h + 16), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((8, 8, 8 + w, 8 + h), radius=w // 2, fill=(70, 150, 255, 235), outline=(20, 60, 160, 255), width=3)
    d.rounded_rectangle((8 + w * .25, 14, 8 + w * .45, 8 + h - 10), radius=4, fill=(215, 240, 255, 230))
    return im

def draw_tears(canvas, t, dur, eyes, scale=1.0):
    """eyes: [(x,y),(x,y)] in output-canvas coordinates."""
    a = 1 - ease_in_cubic((t - (dur - .2)) / .2)
    grow = ease_out_cubic(t / .5)
    for j, (ex, ey) in enumerate(eyes):
        h = int((230 + 30 * math.sin(t * 9 + j)) * grow * scale) + 10
        sp = tear_stream(max(12, h), int(48 * scale))
        wob = 3 * math.sin(t * 14 + j * 2)
        paste_scaled(canvas, sp, ex + wob, ey + sp.height / 2 - 8, 1.0, 0, a)

# ---------------- dizzy ring + stars ----------------
@functools.lru_cache(None)
def star_sprite(r, col):
    im = Image.new('RGBA', (r * 2 + 10, r * 2 + 10), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    pts = []
    for i in range(10):
        ang = -math.pi / 2 + i * math.pi / 5; rr = r if i % 2 == 0 else r * .45
        pts.append((r + 5 + rr * math.cos(ang), r + 5 + rr * math.sin(ang)))
    d.polygon(pts, fill=col, outline=(30, 30, 30, 255)); d.line(pts + [pts[0]], fill=(30, 30, 30, 255), width=3)
    return im

def draw_dizzy(canvas, t, dur, cx, cy, rx=170):
    ry = rx * .28
    k = ease_out_back(t / .25, 2.0); a = 1 - ease_in_cubic((t - (dur - .2)) / .2)
    s = k * (1 - .4 * (1 - a))
    layer = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(layer)
    for wdt, col in ((9, (20, 20, 20, 255)), (4, (255, 255, 255, 255))):
        d.ellipse((cx - rx * s, cy - ry * s, cx + rx * s, cy + ry * s), outline=col, width=wdt)
    cols = [(255, 220, 40, 255), (60, 230, 220, 255), (255, 255, 255, 255), (255, 220, 40, 255), (60, 230, 220, 255)]
    stars = []
    for i in range(5):
        ang = t * 4.5 + i * 2 * math.pi / 5
        x, y = cx + rx * s * math.cos(ang), cy + ry * s * math.sin(ang)
        depth = (math.sin(ang) + 1) / 2
        stars.append((depth, x, y, cols[i]))
    for depth, x, y, col in sorted(stars):
        paste_scaled(layer, star_sprite(26, col), x, y, s * (.7 + .5 * depth), 0, 1)
    if a < 1:
        layer.putalpha(layer.getchannel('A').point(lambda v: int(v * a)))
    canvas.alpha_composite(layer)

# ---------------- sticker (emoji + slanted text) ----------------
@functools.lru_cache(None)
def sticker_image(emoji, text):
    ef = ImageFont.truetype(EMOJI_FONT, 109)
    e = Image.new('RGBA', (140, 140), (0, 0, 0, 0)); ImageDraw.Draw(e).text((6, 6), emoji, font=ef, embedded_color=True)
    e = e.crop(e.getbbox()).resize((190, 190), Image.LANCZOS)
    # white die-cut border around emoji
    m = e.getchannel('A').filter(ImageFilter.MaxFilter(13))
    border = Image.new('RGBA', e.size, (255, 255, 255, 255)); border.putalpha(m)
    border = border.resize((border.width, border.height))
    em = Image.new('RGBA', (e.width + 20, e.height + 20), (0, 0, 0, 0))
    sh = Image.new('RGBA', em.size, (0, 0, 0, 0)); sh.paste((0, 0, 0, 110), (6, 9), m)
    em.alpha_composite(sh.filter(ImageFilter.GaussianBlur(4))); em.alpha_composite(border, (4, 4)); em.alpha_composite(e, (4, 4))
    lines = text.split('\n')
    timgs = [shadowed_text(l, font(STICK_FONT, 74), stroke=7, shadow=(4, 6), shadow_alpha=160, blur=2) for l in lines]
    tw = max(i.width for i in timgs); th = sum(i.height - 18 for i in timgs)
    out = Image.new('RGBA', (max(tw, em.width) + 20, em.height + th + 10), (0, 0, 0, 0))
    out.alpha_composite(em, ((out.width - em.width) // 2, 0))
    y = em.height - 30
    for im in timgs:
        out.alpha_composite(im, ((out.width - im.width) // 2, y)); y += im.height - 18
    return out

def draw_sticker(canvas, t, dur, emoji, text, cx, cy, rot=-8):
    k = (t - 0) / .28
    s = ease_out_back(k, 2.6)
    out_k = (t - (dur - .18)) / .18
    if out_k > 0: s *= 1 - ease_in_cubic(out_k)
    wob = 4 * math.sin(t * 5.5) * (1 - clamp(k - 1) * 0) if k >= 1 else 0
    paste_scaled(canvas, sticker_image(emoji, text), cx, cy + 6 * math.sin(t * 3), s, rot + wob, 1)

# ---------------- title card ----------------
def _stripe_block(n=5, w=70, gap=38, h=260, skew=120):
    """black diagonal parallelogram stripes (chevron-ish bars)."""
    tot = n * (w + gap) + skew
    im = Image.new('RGBA', (tot + 10, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for i in range(n):
        x = i * (w + gap)
        d.polygon([(x + skew, 0), (x + skew + w, 0), (x + w, h), (x, h)], fill=(15, 15, 15, 255))
    return im

STRIPES = None
def _phone_icon(size=230):
    im = Image.new('RGBA', (size, size), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    pw, ph = size * .46, size * .82
    x0, y0 = size * .30, size * .08
    d.rounded_rectangle((x0, y0, x0 + pw, y0 + ph), radius=16, outline=(15, 15, 15, 255), width=7, fill=(255, 255, 255, 255))
    d.rounded_rectangle((x0 + pw * .35, y0 + 10, x0 + pw * .65, y0 + 20), radius=4, fill=(15, 15, 15, 255))
    # wrench crossing the phone
    cx, cy = size * .33, size * .62
    wr = Image.new('RGBA', (size, size), (0, 0, 0, 0)); dw = ImageDraw.Draw(wr)
    dw.rounded_rectangle((cx - 9, cy - 70, cx + 9, cy + 40), radius=8, fill=(15, 15, 15, 255))
    dw.ellipse((cx - 28, cy - 100, cx + 28, cy - 44), fill=(15, 15, 15, 255))
    dw.rectangle((cx - 9, cy - 106, cx + 9, cy - 72), fill=(0, 0, 0, 0))
    wr = wr.rotate(-35, resample=Image.BICUBIC, center=(cx, cy))
    im.alpha_composite(wr)
    return im

def _skew(img, k=-0.22):
    w, h = img.size; dx = abs(k) * h
    return img.transform((int(w + dx), h), Image.AFFINE, (1, k, k * h if k < 0 else 0, 0, 1, 0), Image.BICUBIC)

@functools.lru_cache(None)
def title_parts(l1, l2):
    f = font(TITLE_FONT, 138)
    def t(s):
        im = shadowed_text(s, f, fill=(15, 15, 15, 255), shadow=(0, 0), shadow_alpha=0, pad=10)
        return _skew(im)
    chev = shadowed_text('»', font(TITLE_FONT, 120), fill=(15, 15, 15, 255), shadow_alpha=0)
    return t(l1), t(l2), chev, _phone_icon()

def draw_title_card(canvas, t, dur, l1='ICORE', l2='SERVIS PODCAST'):
    global STRIPES
    if STRIPES is None: STRIPES = _stripe_block()
    canvas.paste((250, 250, 250, 255), (0, 0, W, H))
    kin = ease_out_quint(t / .30); kout = ease_in_cubic((t - (dur - .22)) / .22)
    # stripes slide in diagonally from the corners, out the opposite way
    off = (1 - kin) * 700 + kout * -900
    sx, sy = 0 - 60 + off * -1, 40 + off * -0.55
    _safe_composite(canvas, STRIPES, int(sx - 40), int(sy))
    _safe_composite(canvas, STRIPES, int(W - STRIPES.width + 40 - off * -1), int(H - STRIPES.height - 40 - off * -0.55))
    t1, t2, chev, icon = title_parts(l1, l2)
    cy = H / 2
    a = 1 - kout
    k1 = ease_out_back((t - .06) / .22, 2.2); k2 = ease_out_back((t - .16) / .22, 2.2); k3 = ease_out_back((t - .24) / .22, 2.4)
    paste_scaled(canvas, icon, W / 2 + 230, cy - 170, k3 * (1 - .3 * kout), 6 * math.sin(t * 6), a)
    paste_scaled(canvas, chev, W / 2 - t1.width / 2 - 70, cy - 10, k1, 0, a)
    paste_scaled(canvas, t1, W / 2 - 30, cy - 10, k1, 0, a)
    paste_scaled(canvas, t2, W / 2, cy + 125, k2, 0, a)
    paste_scaled(canvas, chev, W / 2 + t2.width / 2 - 20, cy + 230, k2 * .8, 0, a)
