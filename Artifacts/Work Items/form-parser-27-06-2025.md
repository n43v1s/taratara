# Work Item: Google Form Parser Service — 27-06-2025

## Status: Completed

## Yang Dilakukan

Membangun service untuk fetch dan parse Google Form HTML, mengekstrak semua field metadata.

## File Yang Dibuat

| File | Keterangan |
|---|---|
| `app/services/form_parser.py` | Service fetch + parse Google Form |
| `app/routers/form.py` | Route `GET /form/` dan `POST /form/parse` |
| `app/templates/form.html` | Halaman input URL dan hasil parsing |

## Teknik Parsing

- Data diambil dari variabel JS `FB_PUBLIC_LOAD_DATA_` yang di-embed Google di HTML form
- Bracket counter digunakan untuk mengekstrak array bersarang yang besar (bukan regex greedy)
- Struktur data: `raw[1][1]` = daftar field; setiap field: `[id, label, null, type_code, [sub_items]]`
- Sub-item: `[entry_id, options_or_null, ...]`
- Fallback DOM extraction tersedia jika `FB_PUBLIC_LOAD_DATA_` tidak ditemukan

## Perbaikan yang Dilakukan Selama Development

- Regex awal `\[.+?\]` gagal untuk nested array besar → diganti bracket counter
- DOM fallback mengambil `_sentinel` fields → DOM fallback tetap ada tapi tidak dipakai jika JSON berhasil
- Validasi URL diperluas untuk menerima `https://forms.gle/` selain `https://docs.google.com/forms/`
- `TemplateResponse` signature diupdate ke Starlette 1.3.1 API

## Verifikasi (URL: https://forms.gle/FEjxvFgDF4pXQR5f7)

- Form ID: `1FAIpQLSf9H1VIeE4PgzlPa4shzJNylPsrBVgEUtWvr1GOLgsQDsS_6A` ✓
- Response URL: terdeteksi benar ✓
- fbzx: terdeteksi ✓
- 11 field terdeteksi: Nama Anak, Tempat Tanggal Lahir, Usia Anak, Jenis Kelamin, Agama, Nama Ortu, Satker, No Hp, Alamat, Alergi, Tanggal Booking ✓
- Tipe field benar: short_text dan checkbox ✓
- Opsi checkbox terdeteksi: Usia (2 opsi), Jenis Kelamin (2 opsi), Tanggal Booking (4 tanggal) ✓
- Hasil disimpan ke `data/form-profile.json` ✓
