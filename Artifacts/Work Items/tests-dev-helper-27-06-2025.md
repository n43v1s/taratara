# Work Item: Test Suite & Dev Helper — 27-06-2025

## Status: Completed

## Yang Dilakukan

Membangun test suite otomatis dan dev startup helper.

## File Yang Dibuat

| File | Keterangan |
|---|---|
| `tests/__init__.py` | Package marker |
| `tests/test_form_parser.py` | 11 test: parse fields, label, entry ID, options, tipe, fbzx, error handling |
| `tests/test_field_matcher.py` | 7 test: exact alias, typo match, unmapped, result structure |
| `tests/test_config_handler.py` | 6 test: validate config, save/read config, save/read form profile |
| `tests/test_validator.py` | 7 test: ready state, blocking conditions, booking date validation |
| `scripts/dev.ps1` | Aktifkan .venv + jalankan uvicorn dalam satu perintah |

## Hasil Test

```
30 passed in 0.25s
```

## Cara Jalankan

```powershell
# Aktifkan venv dulu
.\.venv\Scripts\Activate.ps1

# Jalankan semua test
pytest tests/ -v

# Atau gunakan dev helper untuk start server
.\scripts\dev.ps1
```
