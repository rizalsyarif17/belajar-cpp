# Catatan Gaya Edit — dari Video Referensi

Sumber: video vertikal 576×1024, 30 fps, 150,9 detik. Format vlog servis HP: kamera statis dari sudut pandang teknisi, pelanggan duduk di seberang meja, tangan teknisi masuk ke frame.

## 1. Layout (tetap sepanjang video)
- **Format 9:16 penuh.** Footage mengisi seluruh frame, tanpa border dan tanpa blur background.
- **Kotak watermark/info toko:** posisi tetap di sekitar 66–72% tinggi frame, rata tengah, lebar ±48% frame.
  - Kotak putih solid (#FFFFFF, opasitas ±95%), sudut tajam, tanpa bayangan.
  - Teks 2 baris warna hitam, font **serif** (gaya Times New Roman), ukuran ±3% tinggi frame, rata tengah.
  - Baris 1: handle akun, baris 2: lokasi.
  - Selalu tampil dari awal sampai akhir, tanpa animasi (statis).
- **Caption ucapan:** di sekitar 82–84% tinggi frame, rata tengah, di bawah kotak watermark.

## 2. Caption (gaya utama)
- Font **sans-serif tebal kapital** (gaya Montserrat ExtraBold / Arial Black), ukuran kecil ±2,2% tinggi frame.
- Teks putih dengan outline/shadow tipis gelap supaya terbaca di latar putih.
- **Word-by-word highlight:** 2–4 kata tampil per potongan; kata yang sedang diucapkan diberi **kotak ungu solid** (#7B2FF7 / ungu-violet) dengan teks putih, sudut sedikit membulat, padding kecil.
- Highlight pindah per kata mengikuti ucapan (karaoke).
- Animasi masuk: pop kecil (skala ±90%→100% dalam 3–4 frame), tanpa animasi keluar (langsung diganti potongan berikutnya).
- Maksimal 2 baris; ditulis sesuai ucapan asli (bahasa santai).

## 3. Jenis Adegan (pilih bebas sesuai isi, bukan urutan wajib)
| Kode | Jenis | Ciri |
|---|---|---|
| A | **Talking/aksi normal** | Footage apa adanya + watermark + caption. Paling sering muncul (±75% durasi). |
| B | **Punch-in zoom** | Zoom ke wajah 115–135% saat momen reaksi/punchline. Masuk cepat (4–6 frame, ease-out), tahan 1–3 detik, keluar dengan hard cut kembali ke 100%. |
| C | **Overlay efek emosi full-frame** | Lapisan grafis transparan di atas footage: hati pixel pink + tint pink (momen manis/terkesan), teks "Crying/Sobbing…" bergerak + air mata kartun di wajah (momen sedih/lebay). Durasi 2–4 detik, masuk fade/pop, keluar cut. |
| D | **Stiker/meme kecil** | Stiker meme (kucing, emoji) + teks miring putih outline hitam ("BT PARAH…", "NGELUNJAK"), ditempel dekat wajah. Masuk pop + sedikit goyang, tahan 2–4 detik. |
| E | **Efek kepala/wajah** | Bintang/lingkaran pusing di atas kepala, efek wajah lucu (face-warp) 1–2 detik untuk reaksi. |
| F | **Kartu judul/bumper** | Latar putih polos + strip garis miring hitam di pojok kiri atas & kanan bawah (meluncur masuk), logo + judul font **italic condensed tebal hitam** dengan panah "»" kecil. Durasi ±1,5 detik, dipakai sebagai jeda/segmen pemisah. |
| G | **Filter grayscale/flash** | Desaturasi singkat (hitam-putih) untuk momen dramatis/kecewa, 1–2 detik. |

## 4. Transisi & Gerak Kamera
- Dominan **hard cut** (jump cut) untuk membuang jeda/hening.
- Ke/dari kartu judul (F): **whip/slide** cepat (garis miring meluncur masuk dari diagonal), 6–8 frame.
- Zoom selalu pakai ease (cepat di awal, melambat di akhir) — tidak linear supaya tidak kaku.
- Sesekali pergeseran framing (zoom 100→110% pelan) saat berganti potongan agar jump cut tidak terasa patah.

## 5. Ritme
- Rata-rata ganti potongan/efek setiap **2–4 detik**.
- Caption ganti setiap **0,5–1,2 detik**.
- Efek overlay/stiker muncul kira-kira setiap **10–20 detik**, hanya di momen reaksi yang cocok.
- Kartu judul (F) jarang: 1 kali per ±1–2 menit.

## 6. Audio
- Loudness akhir referensi: **-12,8 LUFS integrated** (cocok untuk TikTok/Reels), peak ±0 dBFS → target ekspor: **-13 LUFS, true peak -1 dBTP**.
- Suara asli (voice) dominan.
- **Musik latar:** lagu santai/lucu, diletakkan ±18–22 dB di bawah voice (kira-kira -32 sampai -35 LUFS sendiri), naik ke ±-10 dB relatif saat kartu judul / bagian tanpa ucapan, ducking otomatis saat ada suara.
- **SFX:** pop/whoosh untuk stiker & transisi, "ding"/sparkle untuk hati, suara nangis lebay untuk overlay sedih — level ±6–10 dB di bawah puncak voice, durasi pendek, tidak menimpa kata penting.

## 7. Warna
- Grading natural, sedikit lebih terang dan hangat, saturasi normal; kulit cerah.
- Warna aksen grafis: ungu (#7B2FF7) untuk highlight caption, pink/magenta untuk overlay hati, hitam-putih untuk kartu judul.
