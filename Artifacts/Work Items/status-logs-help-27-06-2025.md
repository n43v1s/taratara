# Work Item: Status, Logs & Help Pages — 27-06-2025

## Status: Completed

## Yang Dilakukan

Membangun halaman Status Scheduler, Log & Riwayat, dan Panduan Penggunaan.

## File Yang Dibuat

| File | Keterangan |
|---|---|
| `app/routers/status.py` | Route `GET /status/` |
| `app/routers/logs.py` | Route `GET /logs/` dan `GET /logs/{run_id}` |
| `app/routers/help.py` | Route `GET /help/` |
| `app/templates/status.html` | Status scheduler, log tail, tombol cancel |
| `app/templates/logs.html` | Tabel riwayat semua run |
| `app/templates/log_detail.html` | Detail satu run: ringkasan, hasil attempt, log output |
| `app/templates/help.html` | Panduan 7 langkah, aturan keamanan, navigasi cepat |

## Verifikasi

- Status: scheduler tidak aktif ditampilkan, run terakhir terbaca, log tail 30 baris muncul ✓
- Logs: 2 dry-run tercatat, link "Lihat log" berfungsi ✓
- Help: alur normal 7 langkah, aturan keamanan, kapan parse ulang, navigasi cepat ✓
