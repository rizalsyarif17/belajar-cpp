"""Frame compositor: base.mp4 + plan.json -> video-only render.
Usage: render.py base.mp4 plan.json captions.json out.mp4 [t_start t_end]"""
import sys, json, subprocess, math, time
import numpy as np
from PIL import Image, ImageOps
sys.path.insert(0, __file__.rsplit('/', 1)[0])
import gfx
from gfx import W, H, ease_out_cubic, ease_in_out_cubic, ease_in_cubic, clamp

base, planf, capf, out = sys.argv[1:5]
T0 = float(sys.argv[5]) if len(sys.argv) > 5 else 0
T1 = float(sys.argv[6]) if len(sys.argv) > 6 else None
FPS = 30
plan = json.load(open(planf)); caps = json.load(open(capf))
effects = plan['effects']
hearts, sad = gfx.Hearts(), gfx.SadRows()

def active(t, typ):
    return [e for e in effects if e['type'] == typ and e['t0'] <= t < e['t1']]

def zoom_state(t):
    """returns (scale, cx, cy) in source coords. punch-in: fast ease-out in, hold, eased out or hard cut."""
    s, cx, cy = 1.0, W / 2, H / 2
    for e in effects:
        if e['type'] == 'zoom' and e['t0'] <= t < e['t1']:
            tin = e.get('tin', .18); tout = e.get('tout', 0)
            k = ease_out_cubic((t - e['t0']) / tin)
            if tout and t > e['t1'] - tout: k *= 1 - ease_in_out_cubic((t - (e['t1'] - tout)) / tout)
            # gentle continuing push while holding keeps it alive (not frozen)
            push = 1 + 0.025 * clamp((t - e['t0']) / max(.01, e['t1'] - e['t0']))
            s = (1 + (e['scale'] - 1) * k) * push
            cx = W / 2 + (e['cx'] - W / 2) * k; cy = H / 2 + (e['cy'] - H / 2) * k
        elif e['type'] == 'drift' and e['t0'] <= t < e['t1']:
            k = ease_in_out_cubic((t - e['t0']) / (e['t1'] - e['t0']))
            s = e.get('s0', 1.0) + (e.get('s1', 1.06) - e.get('s0', 1.0)) * k
            cx, cy = e.get('cx', W / 2), e.get('cy', H / 2)
    return s, cx, cy

def crop_box(s, cx, cy):
    w, h = W / s, H / s
    x0 = min(max(cx - w / 2, 0), W - w); y0 = min(max(cy - h / 2, 0), H - h)
    return x0, y0, w, h

def to_screen(pt, box):
    x0, y0, w, h = box
    return ((pt[0] - x0) * W / w, (pt[1] - y0) * H / h), W / w

def main():
    probe = subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', base])
    dur = float(probe)
    t_end = min(T1 or dur, dur)
    nfr = int(round((t_end - T0) * FPS))
    dec = subprocess.Popen(['ffmpeg', '-v', 'error', '-ss', f'{T0:.3f}', '-i', base, '-t', f'{t_end - T0:.3f}',
                            '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE, bufsize=W * H * 3 * 2)
    enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
                            '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '16',
                            '-pix_fmt', 'yuv420p', '-colorspace', 'bt709', '-color_primaries', 'bt709',
                            '-color_trc', 'bt709', '-movflags', '+faststart', out], stdin=subprocess.PIPE)
    st = time.time()
    for i in range(nfr):
        buf = dec.stdout.read(W * H * 3)
        if len(buf) < W * H * 3: break
        t = T0 + i / FPS
        frame = Image.frombuffer('RGB', (W, H), buf, 'raw', 'RGB', 0, 1)
        s, cx, cy = zoom_state(t)
        box = crop_box(s, cx, cy)
        if s > 1.001:
            x0, y0, w, h = box
            frame = frame.resize((W, H), Image.BILINEAR, box=(x0, y0, x0 + w, y0 + h))
        for e in active(t, 'gray'):
            k = min(ease_out_cubic((t - e['t0']) / .12), 1 - ease_in_cubic((t - (e['t1'] - .12)) / .12))
            g = ImageOps.grayscale(frame).convert('RGB')
            g = ImageOps.autocontrast(g, cutoff=1)
            frame = Image.blend(frame, g, k)
        canvas = frame.convert('RGBA')
        for e in active(t, 'hearts'): hearts.draw(canvas, t - e['t0'], e['t1'] - e['t0'])
        for e in active(t, 'sad'): sad.draw(canvas, t - e['t0'], e['t1'] - e['t0'])
        for e in active(t, 'tears'):
            pts = [to_screen(p, box) for p in e['eyes']]
            gfx.draw_tears(canvas, t - e['t0'], e['t1'] - e['t0'], [p for p, _ in pts], pts[0][1] * e.get('scale', 1))
        for e in active(t, 'dizzy'):
            (x, y), sc = to_screen((e['cx'], e['cy']), box)
            gfx.draw_dizzy(canvas, t - e['t0'], e['t1'] - e['t0'], x, y, e.get('rx', 170) * sc)
        for e in active(t, 'sticker'):
            gfx.draw_sticker(canvas, t - e['t0'], e['t1'] - e['t0'], e['emoji'], e['text'], e['cx'], e['cy'], e.get('rot', -8))
        card = active(t, 'card')
        for e in card:
            gfx.draw_title_card(canvas, t - e['t0'], e['t1'] - e['t0'])
        for e in active(t, 'flash'):
            k = 1 - ease_out_cubic((t - e['t0']) / (e['t1'] - e['t0']))
            canvas.alpha_composite(Image.new('RGBA', (W, H), (255, 255, 255, int(235 * k))))
        if plan.get('progress') and not card:
            pw = int(W * min(1, (t + 1 / FPS) / plan['total']))
            canvas.paste(tuple(plan['progress']) + (255,), (0, 0, pw, 16))
        if not card:
            for g in caps:
                if g['t0'] <= t < g['t1']:
                    gfx.draw_caption(canvas, g, t); break
        enc.stdin.write(canvas.convert('RGB').tobytes())
        if i % 300 == 0:
            el = time.time() - st
            print(f'{i}/{nfr} frames  {el:.0f}s  eta {el / max(1, i) * (nfr - i):.0f}s', flush=True)
    enc.stdin.close(); enc.wait(); dec.terminate()
    print('done', out)

main()
