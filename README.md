# GestureCanvas

Sebuah real-time digital canvas yang dikendalikan oleh gesture tangan. Proyek ini saya buat untuk mengeksplorasi Computer Vision (CV) dengan Python, tanpa perlu mouse atau stylus. Kamu hanya cukup menggerakkan jari di depan kamera untuk melukis, menghapus, menggeser canvas, hingga mengatur zoom.

Proyek ini dibangun di atas OpenCV dan MediaPipe, dengan pendekatan modular untuk memisahkan logika deteksi tangan dari rendering engine-nya.

![Python](https://img.shields.io/badge/python-3.11-blue)
![OpenCV](https://img.shields.io/badge/OpenCV-4.x-green)
![MediaPipe](https://img.shields.io/badge/MediaPipe-0.10.9-orange)

## Fitur

**Intuitive Gesture Controls** — menggunakan deteksi landmark tangan yang responsif untuk menggambar, menghapus, hingga memindahkan canvas.

**Two-Handed Manipulation** — implementasi pinch-to-zoom menggunakan deteksi dua tangan secara bersamaan.

**Interactive UI Engine** — sistem UI kustom di atas frame OpenCV yang merespons posisi jari (fitur hover-to-select).

**Creative Post-Processing** — Glow & Rainbow FX, efek visual berbasis image blending dan HSV color space.

**Velocity Scaling** — ukuran brush yang dinamis berdasarkan kecepatan gerakan tangan pengguna.

**Mirror Mode** — dukungan simetri untuk menggambar dua sisi sekaligus.

**Utility** — undo system dengan radial progress indicator, dan one-tap save ke PNG.

# Kontrol

Mode utama (index finger): gunakan satu jari telunjuk untuk menggambar, menghapus, atau menggeser posisi canvas tergantung tool yang sedang aktif.

Menu/hover (index + middle): arahkan dua jari ke panel samping untuk memilih tool atau warna. Sistem otomatis melakukan pemilihan setelah hover sekitar 0.3 detik.

Undo (thumb-hold): tunjukkan jempol saja dan tahan sebentar hingga indikator radial di sekitar kursor selesai.

Clear canvas (palm): buka telapak tangan sepenuhnya untuk membersihkan seluruh area canvas seketika.

Zooming (pinch): gunakan kedua tangan sekaligus — aplikasi menghitung jarak antar ujung jari telunjuk untuk melakukan scaling canvas.

Keyboard: `S` untuk save canvas sebagai PNG, `Q` untuk keluar.

# Tech stack

Python 3.11 sebagai bahasa utama. OpenCV menangani video capture, rendering, dan operasi gambar. MediaPipe menangani hand landmark tracking. NumPy dipakai untuk operasi numerik di balik layar (scaling, transformasi koordinat, dan lain-lain).

# Cara menjalankan

```bash
git clone https://github.com/gwenflfr/GestureCanvas.git
cd GestureCanvas
python -m venv venv
venv\Scripts\activate      # Mac/Linux: source venv/bin/activate
pip install -r requirements.txt
python main.py
```

Butuh webcam yang aktif. Dikembangkan dan diuji di Python 3.11.9 MediaPipe belum mendukung Python 3.14, jadi pastikan versi Python-nya sesuai sebelum install.

# Struktur proyek

- `main.py` — loop utama, logika gesture-ke-aksi, pembacaan kamera
- `hand_tracker.py` — wrapper tipis di atas MediaPipe Hands
- `canvas.py` — canvas gambar, panel UI, state, dan semua efek

# Yang masih dikembangkan

Saat ini masih terbatas pada satu kamera default, belum ada pilihan ganti kamera. Belum ada sistem layer, semua tergabung dalam satu canvas flat. Format save juga masih terbatas PNG saja.

Ke depannya berencana menambahkan brush preset dan export sesi menggambar sebagai video, plus custom gesture mapping. Ada juga beberapa bug kecil yang belum sempat dibenahi (kadang hover kepencet dobel kalau tangan sedikit gemetar). Kalau menemukan bug lain, silakan buka issue.

# Lisensi

MIT — silakan fork dan gunakan ulang.

---

Dibuat oleh Gwen, bagian dari eksperimen creative-tech dan computer vision yang sedang berjalan.
