# Work Item: Validation Layer — 27-06-2025

## Status: Completed

## Yang Dilakukan

Membangun service validasi terpusat yang memblokir dry-run dan submit jika kondisi belum terpenuhi.

## File Yang Dibuat

| File | Keterangan |
|---|---|
| `app/services/validator.py` | `check_ready()` dan `check_no_active_scheduler()` |

## Check yang Dijalankan `check_ready()`

1. **Config completeness** — semua required fields terisi di `tara-caraka-form.config.json`
2. **Form parsed** — `form-profile.json` punya `responseUrl`
3. **Mapping confirmed** — semua required internal fields ada di `mappings`
4. **Booking dates valid** — minimal satu dipilih dan ada di opsi form

## Verifikasi

- State lengkap → `ready: True` ✓
- `responseUrl` dikosongkan → `ready: False`, blocking message muncul ✓
- State di-restore setelah test ✓
