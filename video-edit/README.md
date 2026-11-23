# Pipeline edit video (gaya referensi)

Script yang dipakai untuk mengedit IMG_0194 menjadi ±3 menit dengan gaya di `docs/style-guide-video.md`.

1. `transcribe.py` – transkrip + timestamp per kata (faster-whisper, model `medium`, bahasa `id`).
2. `build_plan.py spec.json outdir` – rentang isi yang dipilih → jump cut otomatis (VAD), caption per kata, efek & SFX (ditulis dalam waktu sumber, dipetakan ke waktu output).
3. `build_base.py raw.mov plan.json workdir` – potong RAW (HLG/HDR) → 1080×1920, 30 fps, SDR.
4. `render.py base.mp4 plan.json captions.json out.mp4` – compositor per frame: zoom ber-easing, grayscale, hati pixel, teks sedih, efek pusing, stiker, kartu judul, caption highlight ungu.
5. `synth_audio.py` – musik latar & SFX buatan sendiri (bebas lisensi).
6. `mix.py voice.wav plan.json audio_dir out.wav` – voice + musik (ducking) + SFX → -13 LUFS / -1 dBTP.

Jenis adegan dipilih dari isi ucapan (lihat `spec_IMG_0194.json`), bukan urutan tetap.
