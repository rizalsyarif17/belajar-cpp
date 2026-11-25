"""Audio mix: voice + ducked music + SFX -> -13 LUFS / -1 dBTP.
Usage: mix.py voice.wav plan.json assets_audio_dir out.wav"""
import sys, json, subprocess, re
voice, planf, adir, out = sys.argv[1:5]
plan = json.load(open(planf))

def lufs(path, extra=''):
    o = subprocess.run(['ffmpeg', '-nostats', '-i', path, '-af', (extra + ',' if extra else '') + 'ebur128=peak=true',
                        '-f', 'null', '-'], capture_output=True, text=True).stderr
    I = float(re.findall(r'I:\s+(-?[\d.]+) LUFS', o)[-1])
    return I

def dur(p):
    return float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', p]))

D = dur(voice)
VOICE_T = -16.0           # voice bus target before final normalisation
MUSIC_REL = plan.get('music_rel', -14.0)   # music bed level vs voice before ducking
v_I = lufs(voice, 'highpass=f=70')
m_I = lufs(f'{adir}/music.wav')
vg = VOICE_T - v_I; mg = VOICE_T + MUSIC_REL - m_I
# SFX loudness targets relative to voice (dB). Short sounds measured by peak, so use per-sound offsets.
SFX_REL = dict(pop=-9, whoosh=-12, swipe=-12, ding=-13, sad=-11, boing=-13, scratch=-14, click=-12, tada=-14)
inputs = ['-i', voice, '-i', f'{adir}/music.wav']
fl = [f"[0:a]highpass=f=70,acompressor=threshold=0.1:ratio=2.5:attack=8:release=120:makeup=1,volume={vg:.2f}dB,asplit=2[v][sc]",
      f"[1:a]atrim=0:{D:.3f},volume={mg:.2f}dB,afade=t=in:d=0.6,afade=t=out:st={max(0, D - 1.8):.3f}:d=1.8[mraw]",
      "[mraw][sc]sidechaincompress=threshold=0.03:ratio=2:attack=30:release=500:makeup=1[m]"]
mixins = ['[v]', '[m]']
sfx_I = {}
for i, s in enumerate(plan.get('sfx', [])):
    n = s['name']
    if n not in sfx_I:
        sfx_I[n] = lufs(f'{adir}/{n}.wav', 'apad=pad_dur=0.6')  # pad so short sounds get a gated reading
    idx = len(inputs) // 2
    inputs += ['-i', f'{adir}/{n}.wav']
    g = VOICE_T + SFX_REL.get(n, -12) + s.get('gain', 0) - sfx_I[n]
    ms = int(s['t'] * 1000)
    fl.append(f"[{idx}:a]volume={g:.2f}dB,adelay={ms}|{ms}[s{i}]")
    mixins.append(f'[s{i}]')
import os
stem = os.environ.get('STEM')
wts = ' '.join(('1' if (stem is None or (stem == 'voice' and k == 0) or (stem == 'music' and k == 1) or (stem == 'sfx' and k > 1)) else '0') for k in range(len(mixins)))
fl.append(''.join(mixins) + f"amix=inputs={len(mixins)}:normalize=0:dropout_transition=0:weights='{wts}',atrim=0:{D:.3f}[mix]")
if stem:
    subprocess.check_call(['ffmpeg', '-v', 'error', '-y', *inputs, '-filter_complex', ';'.join(fl), '-map', '[mix]',
                           '-ar', '48000', '-c:a', 'pcm_f32le', out]); sys.exit()
pre = out.replace('.wav', '_pre.wav')
subprocess.check_call(['ffmpeg', '-v', 'error', '-y', *inputs, '-filter_complex', ';'.join(fl), '-map', '[mix]',
                       '-ar', '48000', '-c:a', 'pcm_f32le', pre])
# final loudness: two-pass loudnorm to -13 LUFS integrated, -1 dBTP (reference measured -12.8 LUFS)
o = subprocess.run(['ffmpeg', '-nostats', '-i', pre, '-af', 'loudnorm=I=-13:TP=-1:LRA=11:print_format=json',
                    '-f', 'null', '-'], capture_output=True, text=True).stderr
js = json.loads(o[o.rfind('{'):o.rfind('}') + 1])
af = (f"loudnorm=I=-13:TP=-1:LRA=11:measured_I={js['input_i']}:measured_TP={js['input_tp']}:"
      f"measured_LRA={js['input_lra']}:measured_thresh={js['input_thresh']}:offset={js['target_offset']}:linear=true")
subprocess.check_call(['ffmpeg', '-v', 'error', '-y', '-i', pre, '-af', af + ',aresample=48000', '-c:a', 'pcm_s16le', out])
print('voice gain', round(vg, 1), 'music gain', round(mg, 1), 'final I', lufs(out))
