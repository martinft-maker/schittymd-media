# Pipeline – schittymd

- `schitty.py` – karusell-renderer. `python3 schitty.py render diagnoser.jsonl 015,016 OUTDIR` gir OUTDIR/schittymd_NNN_1..7.png
- `diagnoser.jsonl` – én diagnose per linje (id, navn, icd, rammer, definisjon, symptomer, arsaker, kriterier, behandling, hook)
- `used_ids.txt` – brukte ID-er

Ingen emojier i brødtekst (fonten mangler dem). Emojier kun i overskrifter (lagt inn av rendreren) og i hook-linjen.
