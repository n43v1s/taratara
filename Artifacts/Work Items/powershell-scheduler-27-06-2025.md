# Work Item: PowerShell Scheduler Script — 27-06-2025

## Status: Completed (DryRun verified)

## Yang Dilakukan

Membangun `tara-caraka-form.ps1` — script background scheduler untuk submit Google Form.

## File Yang Dibuat

| File | Keterangan |
|---|---|
| `tara-caraka-form.ps1` | PowerShell scheduler dengan mode DryRun dan Submit |

## Fitur

- Mode `DryRun`: build payload, cetak preview, tidak kirim
- Mode `Submit`: buat lock file, cegah laptop sleep, kirim 3 attempt (12:59:58, 12:59:59, 13:00:00)
- Baca config dari `data/tara-caraka-form.config.json` dan `data/form-profile.json`
- Payload di-URL-encode dengan `[System.Uri]::EscapeDataString`
- Checkbox fields (bookingDates) dikirim sebagai multiple entry dengan key yang sama
- Sleep prevention via `SetThreadExecutionState` (Windows API)
- Lock file di `data/scheduler.lock` — cegah duplicate submit
- Run record disimpan ke `data/runs/`, log ke `data/logs/`

## Perbaikan Selama Development

- `@"..."@` diganti `@'...'@` untuk C# here-string — menghindari variable expansion dan parse error
- `-join "&"` diganti `[string]::Join("&", $BodyParts)` — menghindari `&` diparsing sebagai operator PS5

## Verifikasi DryRun

```
Run ID  : run-20260627-053300-a2f231
Payload : 10 field ter-encode dengan benar
Tanggal : entry.1384292428 muncul 4 kali (2 Juni, 3 Juni, 4 Juni, 5 Juni)
Status  : SUCCESS (DryRun) — form tidak dikirim
```
