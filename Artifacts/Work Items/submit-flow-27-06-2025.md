# Work Item: Submit Flow (Prepare → Confirm → Cancel) — 27-06-2025

## Status: Completed (UI verified, Submit belum ditest sungguhan)

## Yang Dilakukan

Membangun alur submit dua langkah: Prepare (review) → Confirm (jalankan scheduler).

## File Yang Dibuat

| File | Keterangan |
|---|---|
| `app/routers/submit.py` | Route prepare, confirm, cancel |
| `app/templates/submit_prepare.html` | Halaman review lengkap + tombol Confirm merah |
| `app/templates/submit_result.html` | Halaman hasil setelah confirm atau cancel |

## Fitur

- `GET /submit/prepare` — tampilkan ringkasan: endpoint, form ID, jadwal attempt, semua field + nilai
- `POST /submit/confirm` — cek validator + lock, launch PowerShell sebagai background process (`CREATE_NEW_CONSOLE`), simpan run record
- `POST /submit/cancel` — hapus lock file, update run record status ke `cancelled`
- Jika scheduler sedang aktif → tombol Confirm disembunyikan, tombol Cancel muncul
- Jika validasi belum siap → blocking issues ditampilkan + link ke form/mapping/config/dryrun

## Verifikasi UI

- Halaman Prepare tampil dengan ringkasan lengkap ✓
- Field name + entry ID + nilai semua benar ✓
- Tanggal booking muncul sebagai 4 baris terpisah ✓
- Tombol Confirm Submit merah dengan peringatan ✓
- Submit sungguhan belum ditest (menunggu waktu booking yang tepat)
