"""Cut segments from the RAW (HLG HEVC) into a 1080x1920/30fps SDR base + voice wav.
Usage: build_base.py raw.mov plan.json workdir"""
import sys, json, subprocess, os
raw, planf, wd = sys.argv[1:4]
os.makedirs(wd, exist_ok=True)
plan = json.load(open(planf))
FPS = 30
GRADE = ",eq=contrast=1.04:saturation=1.07:brightness=0.012:gamma=1.02,colorbalance=rs=0.015:bs=-0.015:rm=0.01:bm=-0.01"
VF0 = ("tpad=stop_mode=clone:stop_duration=0.2,scale=1080:1920:flags=lanczos,fps=30,format=yuv420p,"
      )
VF = VF0.rstrip(',') + (GRADE if plan.get('grade', True) else '')
if plan.get('vf_pre'): VF = plan['vf_pre'] + ',' + VF
parts = []
for i, s in enumerate(plan['segments']):
    v = f'{wd}/seg{i:03d}.mp4'
    if 'card' in s:
        d = s['card']
        cmd = ['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i', f'color=c=white:s=1080x1920:r=30:d={d}',
               '-f', 'lavfi', '-i', f'anullsrc=r=48000:cl=stereo', '-t', f'{d}', '-frames:v', str(round(d * FPS)),
               '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '14', '-pix_fmt', 'yuv420p',
               '-c:a', 'pcm_s16le', v.replace('.mp4', '.mov')]
    elif s.get('speed'):
        sp = s['speed']; d = round((s['src1'] - s['src0']) / sp * FPS) / FPS
        cmd = ['ffmpeg', '-v', 'error', '-y', '-ss', f"{s['src0']:.3f}", '-t', f"{s['src1'] - s['src0'] + 0.3:.3f}", '-i', raw,
               '-f', 'lavfi', '-i', 'anullsrc=r=48000:cl=stereo', '-map', '0:v:0', '-map', '1:a:0',
               '-vf', f'setpts=PTS/{sp},' + VF, '-frames:v', str(round(d * FPS)), '-t', f'{d:.4f}',
               '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '14', '-c:a', 'pcm_s16le', v.replace('.mp4', '.mov')]
    else:
        d = s['src1'] - s['src0']
        af = f"afade=t=in:d=0.012,afade=t=out:st={d - 0.015:.3f}:d=0.015"
        cmd = ['ffmpeg', '-v', 'error', '-y', '-ss', f"{s['src0']:.3f}", '-i', raw, '-t', f'{d:.3f}',
               '-map', '0:v:0', '-map', '0:a:0', '-vf', VF, '-frames:v', str(round(d * FPS)), '-af', af, '-ar', '48000', '-ac', '2',
               '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '14', '-c:a', 'pcm_s16le', v.replace('.mp4', '.mov')]
    if not os.path.exists(v.replace('.mp4', '.mov')) or '--force' in sys.argv:
        subprocess.check_call(cmd)
    parts.append(v.replace('.mp4', '.mov'))
with open(f'{wd}/list.txt', 'w') as f:
    for p in parts: f.write(f"file '{os.path.abspath(p)}'\n")
subprocess.check_call(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', f'{wd}/list.txt',
                       '-c:v', 'copy', '-an', f'{wd}/base.mp4'])
subprocess.check_call(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', f'{wd}/list.txt',
                       '-vn', '-c:a', 'pcm_s16le', f'{wd}/voice.wav'])
print('base ok')
