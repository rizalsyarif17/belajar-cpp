"""Voice track matching build_base segments exactly (frame-accurate). Speed/card segments -> silence.
Usage: build_voice.py raw plan.json workdir"""
import sys, json, subprocess, os
raw, planf, wd = sys.argv[1:4]
plan = json.load(open(planf)); os.makedirs(f'{wd}/wa', exist_ok=True); fl = []
g = plan.get('raw_audio_gain', 0)
for i, s in enumerate(plan['segments']):
    o = f'{wd}/wa/a{i:03d}.wav'
    if 'card' in s or s.get('speed'):
        d = round((s['card'] if 'card' in s else (s['src1'] - s['src0']) / s['speed']) * 30) / 30
        cmd = ['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i', 'anullsrc=r=48000:cl=stereo', '-t', f'{d:.4f}', '-c:a', 'pcm_s16le', o]
    else:
        d = round((s['src1'] - s['src0']) * 30) / 30
        af = (f"aresample=48000,volume={g}dB,afade=t=in:d=0.012,afade=t=out:st={d - 0.015:.4f}:d=0.015,"
              f"apad=whole_dur={d:.4f},atrim=0:{d:.4f}")
        cmd = ['ffmpeg', '-v', 'error', '-y', '-ss', f"{s['src0']:.4f}", '-i', raw, '-t', f'{d + 0.1:.4f}', '-vn', '-ac', '2',
               '-af', af, '-c:a', 'pcm_s16le', o]
    subprocess.check_call(cmd); fl.append(os.path.abspath(o))
open(f'{wd}/wa/list.txt', 'w').write(''.join(f"file '{f}'\n" for f in fl))
subprocess.check_call(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', f'{wd}/wa/list.txt', '-c:a', 'pcm_s16le', f'{wd}/voice.wav'])
print('voice ok')
