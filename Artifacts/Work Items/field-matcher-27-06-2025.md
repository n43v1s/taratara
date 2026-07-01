# Work Item: Field Matching Service — 27-06-2025

## Status: Completed

## Yang Dilakukan

Membangun service untuk mencocokkan label Google Form ke internal field names secara otomatis.

## File Yang Dibuat

| File | Keterangan |
|---|---|
| `app/services/field_matcher.py` | Service matching: alias lookup + rapidfuzz, output confidence + status |

## Logika Matching

1. **Normalisasi label**: lowercase, trim, hapus spasi berlebih, hapus tanda baca
2. **Layer 1 — Exact alias match**: dibandingkan ke semua alias di `field-aliases.json` (score 100, status `auto`)
3. **Layer 2 — Fuzzy match**: `fuzz.token_sort_ratio` dibandingkan ke semua alias semua field
   - Score ≥ 90% → status `auto`
   - Score 75–89% → status `suggest`
   - Score < 75% → status `unmapped`, `internalField` kosong

## Verifikasi

### Form 1 (https://forms.gle/FEjxvFgDF4pXQR5f7) — 11 field
Semua 11 field → 100% auto ✓

### Form 2 (https://docs.google.com/forms/d/e/1FAIpQLSchif_m9SKdxYGzxh8JOeRteHChAaToLJzpiSlm2qfrVh3xUg/viewform) — 10 field
- "Nama Orangtua" → `parentName` 100% auto ✓ (variasi dari "Nama Ortu" di form 1)
- Tidak ada field "Satker" di form 2 → tidak diproses, benar ✓
- Semua 10 field → 100% auto ✓
