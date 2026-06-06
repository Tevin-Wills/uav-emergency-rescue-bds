# Contributing to BDS-SMC2

## Branch naming

| What you're doing | Branch name |
|-------------------|-------------|
| Running Gap 1 experiments | `gap1-encoding` |
| Running Gap 2 latency tests | `gap2-latency` |
| Running Gap 3 field tests | `gap3-field-test` |
| Running Gap 5 encryption | `gap5-aes` |
| Running Gap 6 compression | `gap6-huffman` |
| Any other fix or doc change | `fix/<short-description>` |

## Step-by-step workflow

```bash
# 1. Always pull latest main before starting
git checkout main
git pull origin main

# 2. Create your branch
git checkout -b gap3-field-test

# 3. Do your experiment, add data files
#    e.g. fill in data/gap3_field_test.csv

# 4. Stage only your files (never git add .)
git add data/gap3_field_test.csv
git add Lab7_Report.md

# 5. Commit with a clear message
git commit -m "gap3: add urban environment results (20 TX, 18 delivered)"

# 6. Push your branch
git push origin gap3-field-test

# 7. Open a Pull Request on GitHub and request review from @letsoalomaile1
```

## Data file format

Each experiment appends rows to its CSV in `data/`. Do not delete existing rows.

| File | Columns |
|------|---------|
| `gap1_compression.csv` | mode, ascii_bits, binary_bits, timestamp |
| `gap2_latency.csv` | tx_num, t1_ms, t2_ms, t3_ms, total_ms |
| `gap5_encryption.csv` | tx_num, plaintext_bits, ciphertext_bits, overhead_ms |
| `gap6_telemetry.csv` | tx_num, ascii_bits, binary_bits, huffman_bits |

## Rules

- Never commit to `main` directly — always use a branch + PR
- Never commit `build/` folders or `.bin` files (already in `.gitignore`)
- If you change the firmware, update the `MODE` comment in `esp32_sender.ino`
- If you collect new data, also update the matching section in `Lab7_Report.md`
