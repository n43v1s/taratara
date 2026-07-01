# Work Item: Config Editor — 27-06-2025

## Status: Completed

## Yang Dilakukan

Membangun halaman untuk mengedit nilai default yang akan digunakan saat mengisi Google Form.

## File Yang Dibuat / Diubah

| File | Keterangan |
|---|---|
| `app/routers/config.py` | Route `GET /config/` dan `POST /config/save` |
| `app/templates/config.html` | Form editor dengan validasi real-time via vanilla JS |

## Fitur

- Form dibagi dua card: Data Anak (childName, birthInfo, childAge, gender, religion, allergy) dan Data Orang Tua (parentName, satker, phoneNumber, address)
- Tanggal Booking ditampilkan sebagai checkbox dari opsi yang terdeteksi di form profile
- Field kosong → border merah, field terisi → border hijau (real-time, tanpa reload)
- Banner error di atas diupdate real-time: hilang otomatis saat semua field terisi
- Setelah save: alert hijau + link "Lanjut ke Dry Run" jika semua field lengkap
- Booking dates divalidasi terhadap opsi yang ada di form profile

## Verifikasi

- Validasi real-time berjalan via vanilla JS ✓
- Field terisi → border hijau, kosong → border merah ✓
- Banner missing fields update real-time ✓
- Data tersimpan ke `data/tara-caraka-form.config.json` ✓
- Alert hijau + link Dry Run muncul setelah semua field terisi ✓
