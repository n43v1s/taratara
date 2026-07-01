# Work Item: Field Mapping Review UI — 27-06-2025

## Status: Completed

## Yang Dilakukan

Membangun halaman review dan konfirmasi mapping field Google Form ke internal fields.

## File Yang Dibuat

| File | Keterangan |
|---|---|
| `app/routers/mapping.py` | Route `GET /mapping/` dan `POST /mapping/confirm` |
| `app/templates/mapping.html` | Tabel mapping dengan dropdown per field, badge status, confidence |

## Fitur

- Setiap field ditampilkan dengan label, entry ID, dropdown internal field, confidence, dan status
- Status badge: `auto` (hijau), `suggest` (kuning), `unmapped` (merah), `confirmed` (biru)
- Row `unmapped` diberi highlight kuning sebagai peringatan visual
- Dropdown bisa diubah manual jika hasil otomatis salah
- Setelah submit → status berubah ke `confirmed`, alert hijau muncul, mapping disimpan ke `form-profile.json`
- Jika belum ada form yang di-parse → pesan error + link ke `/form`

## Verifikasi

- 10 field dari form kedua tampil dengan benar ✓
- Semua 100% auto → dropdown terisi otomatis ✓
- Klik "Simpan & Konfirmasi Mapping" → semua status berubah ke `confirmed` ✓
- `form-profile.json` diupdate dengan mappings ✓
- Link "Lanjut ke Config Editor" muncul setelah save ✓
