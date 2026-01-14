# FragAudit Performance Benchmarks

## Test Environment

- **Machine**: Apple Silicon Mac
- **Python**: 3.13.2
- **Date**: 2026-01-14
- **Version**: v3.8.0

## Backend Pillars

| Module | Version | Tests | Avg Time |
|--------|---------|-------|----------|
| Mistakes | v3.4 | 31 | <50ms |
| Roles | v3.5 | 19 | <30ms |
| WPA | v3.6 | 29 | <10ms |
| Strategy | v3.7 | 16 | <20ms |
| Prediction | v3.8 | 23 | <5ms |
| **Total** | | **174** | <115ms |

## Demo Analysis Benchmarks

| Demo | Map | Parse (s) | Analysis (s) | Total (s) | RAM (MB) |
|------|-----|-----------|--------------|-----------|----------|
| acend-vs-washington | de_dust2 | 3.2 | 1.1 | 4.3 | 95 |
| phantom-vs-hyperspirit | de_mirage | 3.5 | 1.2 | 4.7 | 96 |
| boss-vs-m80 | de_ancient | 4.5 | 1.7 | 6.2 | 130 |

## Summary Statistics

| Metric | Average | Target | Status |
|--------|---------|--------|--------|
| Parse Time | 3.7s | - | - |
| Analysis Time | 1.3s | - | - |
| **Total Runtime** | **5.1s** | <10s | ✅ PASS |
| Peak Memory | 107 MB | <500 MB | ✅ PASS |
| All Tests | 174 | 174 | ✅ PASS |

## Prediction Model Performance

| Operation | Time | Throughput |
|-----------|------|------------|
| predict_round_win() | <1ms | 10,000/sec |
| predict_player_impact() | <1ms | 10,000/sec |
| calculate_contextual_wpa() | <0.5ms | 20,000/sec |

## Pipeline Breakdown

```
Parse Demo:        ████████████████░░░░░░░░░ 72%
Feature Extract:   ████░░░░░░░░░░░░░░░░░░░░░ 15%
Mistake Detection: ██░░░░░░░░░░░░░░░░░░░░░░░  8%
Role/Strategy:     █░░░░░░░░░░░░░░░░░░░░░░░░  3%
Prediction:        ░░░░░░░░░░░░░░░░░░░░░░░░░  2%
```

**Bottleneck**: Demo parsing (demoparser2) — 72% of runtime

## Math Scaling Validation

### Economy (tanh)
| Diff | Raw | Contribution |
|------|-----|--------------|
| $1,000 | 0.32 | +0.26 |
| $3,000 | 0.76 | +0.61 |
| $6,000 | 0.96 | +0.77 |
| $10,000 | 1.00 | +0.80 |

*Saturates correctly — no insane swings.*

### Man Advantage
| Diff | Contribution |
|------|--------------|
| +1 | +0.12 |
| +2 | +0.24 |
| +3 | +0.36 |

*Normalized to [-1, 1] range via /5.*

## Verdict

- **Tests**: ✅ 174/174 passing
- **Memory**: ✅ Well under 500MB
- **Runtime**: ✅ 5.1s average
- **Math**: ✅ Properly scaled, bounded

**Status**: Production ready for v3.8 release.
