"""Synthesize royalty-free background music + SFX (48 kHz stereo WAV)."""
import numpy as np, wave, os, sys
SR = 48000
out = sys.argv[1]
os.makedirs(out, exist_ok=True)
rng = np.random.default_rng(7)

def save(name, x):
    x = np.asarray(x, np.float32)
    if x.ndim == 1: x = np.stack([x, x], 1)
    x = x / max(1e-9, np.abs(x).max()) * 0.89
    with wave.open(os.path.join(out, name), 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((x * 32767).astype(np.int16).tobytes())

def t(d): return np.arange(int(d * SR)) / SR
def env(n, a=0.005, d=0.3):
    tt = np.arange(n) / SR
    e = np.minimum(tt / a, 1) * np.exp(-tt / d)
    return e
def mtof(m): return 440 * 2 ** ((m - 69) / 12)

def pluck(freq, dur, bright=0.5):
    n = int(dur * SR); p = max(2, int(SR / freq))
    buf = rng.uniform(-1, 1, p) ; y = np.zeros(n)
    # one-pole lowpass on initial noise for warmth
    for i in range(1, p): buf[i] = bright * buf[i] + (1 - bright) * buf[i - 1]
    idx = 0
    for i in range(n):
        y[i] = buf[idx]
        nxt = (idx + 1) % p
        buf[idx] = 0.996 * 0.5 * (buf[idx] + buf[nxt])
        idx = nxt
    return y * env(n, 0.002, dur * 0.6)

def lp(x, a):
    a = np.broadcast_to(np.asarray(a, float), x.shape)
    y = np.empty_like(x); s = 0.0
    for i in range(len(x)): s += a[i] * (x[i] - s); y[i] = s
    return y

# ---------------- music: playful pluck/marimba lo-fi, 104 BPM ----------------
def music(total=200):
    bpm = 104; beat = 60 / bpm; bar = 4 * beat
    prog = [(60, [0, 4, 7]), (57, [0, 3, 7]), (53, [0, 4, 7]), (55, [0, 4, 7])]  # C Am F G
    n = int(total * SR); L = np.zeros(n); R = np.zeros(n)
    cache = {}
    def note(m, d, kind):
        k = (m, d, kind)
        if k not in cache:
            f = mtof(m)
            if kind == 'pl': cache[k] = pluck(f, d, 0.55)
            elif kind == 'mar':
                tt = t(d); cache[k] = (np.sin(2*np.pi*f*tt) + 0.25*np.sin(2*np.pi*4*f*tt)*np.exp(-tt/0.05)) * env(len(tt), 0.002, 0.25)
            elif kind == 'bass':
                tt = t(d); x = np.sin(2*np.pi*f*tt) + 0.3*np.sin(2*np.pi*2*f*tt)
                cache[k] = x * env(len(tt), 0.01, 0.5)
        return cache[k]
    def add(buf, x, s, g):
        i = int(s * SR); j = min(n, i + len(x))
        if i < n: buf[i:j] += g * x[:j - i]
    kick = np.sin(2*np.pi*np.cumsum(np.linspace(120, 45, int(0.25*SR)))/SR) * env(int(0.25*SR), 0.001, 0.09)
    snap = lp(rng.uniform(-1, 1, int(0.12*SR)), 0.5) * env(int(0.12*SR), 0.001, 0.03)
    hat = (rng.uniform(-1, 1, int(0.05*SR)) - lp(rng.uniform(-1, 1, int(0.05*SR)), 0.3)) * env(int(0.05*SR), 0.0005, 0.012)
    arp_pat = [0, 1, 2, 1, 2, 0, 1, 2]
    mel = [12, 14, 16, 19, 16, 14, 12, None, 9, 12, 14, 12, None, 7, 9, None]
    bars = int(total / bar) + 1
    for b in range(bars):
        root, iv = prog[b % 4]; s0 = b * bar
        add(L, note(root - 24, bar * 0.9, 'bass'), s0, 0.55); add(R, note(root - 24, bar * 0.9, 'bass'), s0, 0.55)
        add(L, note(root - 24 + 7, beat * 1.5, 'bass'), s0 + 2.5 * beat, 0.35); add(R, note(root - 24 + 7, beat * 1.5, 'bass'), s0 + 2.5 * beat, 0.35)
        for k, a in enumerate(arp_pat):
            m = root + iv[a] + (12 if k >= 4 else 0)
            x = note(m, beat, 'pl'); pan = 0.35 + 0.3 * (k % 2)
            add(L, x, s0 + k * beat / 2, 0.32 * (1 - pan)); add(R, x, s0 + k * beat / 2, 0.32 * pan)
        if b >= 2 and (b // 4) % 2 == 1:  # melody every other phrase
            for k in range(8):
                v = mel[(b % 2) * 8 + k]
                if v is not None:
                    x = note(48 + 12 + v + (root - 60 if False else 0), beat, 'mar')
                    add(L, x, s0 + k * beat / 2, 0.18); add(R, x, s0 + k * beat / 2, 0.22)
        for k in range(4):
            if k in (0, 2): add(L, kick, s0 + k * beat, 0.5); add(R, kick, s0 + k * beat, 0.5)
            if k in (1, 3): add(L, snap, s0 + k * beat, 0.22); add(R, snap, s0 + k * beat, 0.25)
        for k in range(8):
            add(R, hat, s0 + k * beat / 2, 0.09 if k % 2 else 0.05); add(L, hat, s0 + k * beat / 2, 0.05)
    x = np.stack([L, R], 1)
    fade = int(2 * SR); x[-fade:] *= np.linspace(1, 0, fade)[:, None]
    return x

# ---------------- SFX ----------------
def sfx_pop():
    d = 0.12; tt = t(d); f = np.linspace(900, 300, len(tt))
    return np.sin(2*np.pi*np.cumsum(f)/SR) * env(len(tt), 0.001, 0.03)
def sfx_whoosh(d=0.45):
    n = int(d*SR); x = rng.uniform(-1, 1, n)
    a = np.linspace(0.02, 0.35, n) ; y = np.empty(n); s = 0
    for i in range(n): s += a[i]*(x[i]-s); y[i] = s
    e = np.sin(np.pi*np.linspace(0, 1, n))**2
    return y * e
def sfx_ding():
    tt = t(1.2); x = 0
    for f, g in [(1568, 1), (2093, .6), (3136, .3), (4186, .15)]:
        x = x + g*np.sin(2*np.pi*f*tt)
    sp = np.zeros_like(tt)
    for k in range(6):
        i = int((0.05 + 0.07*k)*SR); fr = 2500 + 400*k; tt2 = t(0.2)
        s = np.sin(2*np.pi*fr*tt2)*env(len(tt2), 0.001, 0.04)*0.4
        sp[i:i+len(s)] += s[:len(sp)-i]
    return x*env(len(tt), 0.002, 0.35) + sp
def sfx_sad():  # descending "wah wah wah waaah" muted trombone
    out_ = []
    for f, d in [(392, .35), (370, .35), (349, .35), (330, 1.0)]:
        tt = t(d); vib = 1 + 0.012*np.sin(2*np.pi*6*tt)*(d > .5)
        ph = np.cumsum(f*vib)/SR
        x = sum((1/k)*np.sin(2*np.pi*k*ph) for k in range(1, 8))
        wah = 0.5 - 0.5*np.cos(2*np.pi*np.minimum(tt/d, 1))
        out_.append(lp(x, 0.08 + 0.25*wah) * np.minimum(tt/0.03, 1) * np.minimum((d-tt)/0.05, 1))
    return np.concatenate(out_)
def sfx_boing():
    tt = t(0.6); f = 220 + 140*np.sin(2*np.pi*9*tt)*np.exp(-tt/0.25)
    return np.sin(2*np.pi*np.cumsum(f)/SR)*env(len(tt), 0.002, 0.25)
def sfx_record_scratch():
    tt = t(0.35); f = 600 + 500*np.sin(2*np.pi*7*tt)
    x = rng.uniform(-1, 1, len(tt))*0.6 + np.sin(2*np.pi*np.cumsum(f)/SR)*0.4
    return lp(x, 0.3)*env(len(tt), 0.002, 0.15)
def sfx_swipe():  # short bright swish for title card stripes
    return sfx_whoosh(0.28) * 1.0
def sfx_click():
    tt = t(0.05); return np.sin(2*np.pi*2000*tt)*env(len(tt), 0.0005, 0.008)
def sfx_tada():
    tt = t(1.0); x = 0
    for m in (72, 76, 79, 84):
        x = x + np.sign(np.sin(2*np.pi*mtof(m)*tt))*0.25 + np.sin(2*np.pi*mtof(m)*tt)
    return lp(x, 0.2)*env(len(tt), 0.005, 0.4)

if __name__ == '__main__':
    for name, fn in [('pop', sfx_pop), ('whoosh', sfx_whoosh), ('ding', sfx_ding), ('sad', sfx_sad),
                     ('boing', sfx_boing), ('scratch', sfx_record_scratch), ('swipe', sfx_swipe),
                     ('click', sfx_click), ('tada', sfx_tada)]:
        save(name + '.wav', fn())
    save('music.wav', music(float(sys.argv[2]) if len(sys.argv) > 2 else 200))
    print('done')
