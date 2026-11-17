# Pipeline – schittymd

- `schitty.py` – karusell-renderer. `python3 schitty.py render diagnoser.jsonl 015,016 OUTDIR` gir OUTDIR/schittymd_NNN_1..7.png
- `diagnoser.jsonl` – én diagnose per linje (id, navn, icd, rammer, definisjon, symptomer, arsaker, kriterier, behandling, hook)
- `used_ids.txt` – brukte ID-er

Emojier fungerer overalt i teksten (renderer tegner dem med Noto Color Emoji).
