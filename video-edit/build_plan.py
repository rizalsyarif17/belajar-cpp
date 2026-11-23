"""Edit decision list -> plan.json (segments + effects + sfx in OUTPUT time) and captions.json.
Ranges are picked by content; inside each range silences are removed with VAD (jump cuts).
Effects/SFX are authored in SOURCE time (anchored to what is said/seen) and mapped to output time."""
import json, sys, re
RAW = '/tmp/claude-0/-home-user-belajar-cpp/d18ffba8-f99d-5d8b-bae5-b4e8fcb70ea2/scratchpad/raw/'
speech = json.load(open(RAW + 'speech.json'))
words = json.load(open(RAW + 'words.json'))
spec = json.load(open(sys.argv[1]))
outdir = sys.argv[2]
FPS = 30
def fr(x): return round(x * FPS) / FPS

segments, cursor = [], 0.0
mapping = []   # (src0, src1, out0)
for item in spec['timeline']:
    if 'card' in item:
        d = fr(item['card']); segments.append({'card': d, 'out0': cursor}); cursor = fr(cursor + d); continue
    a, b = item['src']
    keep = []
    for s, e in speech:
        s2, e2 = max(s, a), min(e, b)
        if e2 - s2 > 0.12: keep.append([s2, e2])
    for cut in item.get('drop', []):          # manual removals inside a range
        nk = []
        for s, e in keep:
            if e <= cut[0] or s >= cut[1]: nk.append([s, e])
            else:
                if s < cut[0]: nk.append([s, cut[0]])
                if e > cut[1]: nk.append([cut[1], e])
        keep = nk
    # merge pieces separated by tiny gaps, drop slivers
    merged = []
    for s, e in keep:
        if merged and s - merged[-1][1] < 0.18: merged[-1][1] = e
        else: merged.append([s, e])
    for s, e in merged:
        if e - s < 0.35: continue
        s, e = fr(s), fr(e)
        segments.append({'src0': s, 'src1': e, 'out0': cursor})
        mapping.append((s, e, cursor)); cursor = fr(cursor + (e - s))
total = cursor

def s2o(t, snap='near'):
    best = None
    for s, e, o in mapping:
        if s <= t <= e: return o + (t - s)
        # outside: snap to nearest boundary
        d = min(abs(t - s), abs(t - e))
        if best is None or d < best[0]: best = (d, o if abs(t - s) < abs(t - e) else o + (e - s))
    return best[1]

# ---------- captions ----------
FIX = spec.get('fix', {})
cap_words = []
for w in words:
    for mi, (s, e, o) in enumerate(mapping):
        if s - 0.05 <= w['s'] < e:
            txt = w['w'].strip()
            key = txt.lower().strip('?,.!')
            if key in FIX:
                txt = FIX[key]
                if txt is None: break
            elif txt.lower() in FIX:
                txt = FIX[txt.lower()]
                if txt is None: break
            t0 = o + max(0, w['s'] - s); t1 = o + min(e, w['e']) - s
            cap_words.append({'text': txt.strip('?,!'), 't0': round(t0, 3), 't1': round(max(t1, t0 + .12), 3),
                              'src': w['s'], 'srce': w['e'], 'punct': w['w'].strip()[-1:] in '?.,!'})
            break
# merge split tokens like "15" ".6" ".1" and "gara" "-gara"
mw = []
for w in cap_words:
    if mw and (w['text'].startswith('.') or w['text'].startswith('-')) and w['t0'] - mw[-1]['t1'] < .6:
        mw[-1]['text'] += w['text']; mw[-1]['t1'] = w['t1']
    else: mw.append(dict(w))
for o in spec.get('cap_override', []):   # replace words in a source window with given text
    a, b, txt = o
    inside = [w for w in mw if a <= w['src'] < b]
    if not inside: continue
    t0, t1 = inside[0]['t0'], inside[-1]['t1']
    toks = txt.split(); step = (t1 - t0) / len(toks)
    new = [{'text': tk, 't0': round(t0 + i * step, 3), 't1': round(t0 + (i + 1) * step, 3), 'src': a, 'punct': i == len(toks) - 1} for i, tk in enumerate(toks)]
    i0 = mw.index(inside[0]); mw[i0:i0 + len(inside)] = new
    if i0 > 0: mw[i0 - 1]['punct'] = True
OVR = {o[0] for o in spec.get('cap_override', [])}
groups, cur = [], []
for w in mw:
    if cur and (len(cur) >= (4 if cur[0].get('src') in OVR else 3) or w['t0'] - cur[-1]['t1'] > 0.45 or cur[-1].get('punct')
                or w['src'] - cur[-1].get('srce', w['src']) > 0.9 or w['t0'] - cur[0]['t0'] > (2.4 if cur[0].get('src') in OVR else 1.5)
                or sum(len(x['text']) for x in cur) + len(w['text']) > 22):
        groups.append(cur); cur = []
    cur.append(w)
if cur: groups.append(cur)
caps = []
for i, g in enumerate(groups):
    t0 = g[0]['t0'] - 0.04
    nxt = groups[i + 1][0]['t0'] - 0.04 if i + 1 < len(groups) else total
    t1 = min(nxt, g[-1]['t1'] + 0.35)
    caps.append({'t0': round(t0, 3), 't1': round(t1, 3), 'words': [{'text': w['text'], 't0': w['t0'], 't1': w['t1']} for w in g]})
# hide captions while title card is up
cards = [(s['out0'], s['out0'] + s['card']) for s in segments if 'card' in s]
caps = [c for c in caps if not any(a <= c['t0'] < b for a, b in cards)]

# ---------- effects & sfx ----------
effects = []
for s in segments:
    if 'card' in s: effects.append({'type': 'card', 't0': s['out0'], 't1': s['out0'] + s['card']})
for e in spec.get('effects', []):
    e = dict(e)
    if 'src0' in e:
        t0 = s2o(e.pop('src0'))
        t1 = s2o(e.pop('src1')) if 'src1' in e else t0 + e.pop('dur')
        e['t0'], e['t1'] = round(t0, 3), round(t1, 3)
    effects.append(e)
sfx = []
for x in spec.get('sfx', []):
    x = dict(x)
    if 'src' in x: x['t'] = round(s2o(x.pop('src')) + x.pop('off', 0), 3)
    sfx.append(x)
# automatic SFX tied to effect entrances (consistent "in" sounds like the reference)
AUTO = {'sticker': ('pop', 0), 'dizzy': ('boing', 0), 'hearts': ('ding', 0), 'sad': ('sad', 0.05),
        'zoom': ('whoosh', -0.12), 'card': ('swipe', -0.05)}
for e in effects:
    if e.get('nosfx'): continue
    if e['type'] in AUTO:
        n, off = AUTO[e['type']]
        if e['type'] == 'zoom' and e.get('scale', 1) < 1.25: n = 'click'
        sfx.append({'name': n, 't': round(max(0, e['t0'] + off), 3)})
    if e['type'] == 'card': sfx.append({'name': 'whoosh', 't': round(e['t1'] - 0.18, 3)})
plan = {'total': total, 'segments': [{k: v for k, v in s.items() if k != 'out0'} for s in segments],
        'seg_out0': [s['out0'] for s in segments], 'effects': effects, 'sfx': sorted(sfx, key=lambda x: x['t'])}
json.dump(plan, open(outdir + '/plan.json', 'w'), indent=1, ensure_ascii=False)
json.dump(caps, open(outdir + '/captions.json', 'w'), indent=1, ensure_ascii=False)
print(f'total {total:.2f}s, {len([s for s in segments if "src0" in s])} cuts, {len(caps)} caption groups, '
      f'{len(effects)} effects, {len(sfx)} sfx')
# readable timeline
with open(outdir + '/timeline.txt', 'w') as f:
    for s in segments:
        if 'card' in s: f.write(f"{s['out0']:7.2f} CARD {s['card']}\n")
        else: f.write(f"{s['out0']:7.2f} src {s['src0']:.2f}-{s['src1']:.2f}\n")
    for c in caps: f.write(f"  cap {c['t0']:7.2f} {' '.join(w['text'] for w in c['words'])}\n")
