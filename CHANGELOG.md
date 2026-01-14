# Changelog - FragAudit

All notable changes to the CS2 AI Coach project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [3.3.0] - 2026-01-14

### ⚖️ DUAL LICENSE MODEL

Strategic pivot to sustainable open-source.

### Changed
- **License**: Switched to **Dual License** strategy:
  - **GPLv3** for Community/Open Source usage
  - **Commercial License** for proprietary/closed-source usage
- **README**: Updated badging and license sections
- **Docs**: Added `docs/COMMERCIAL.md`

## [3.1.0] - 2026-01-13

### 🔓 OPEN SOURCE EDITION

Major release switching to MIT license and focusing on usability.

### Changed
- **License**: Confirmed **MIT** — use it however you want
- **README**: Complete rewrite — honest, no buzzwords, clear limitations
- **Output Format**: Mistakes now show round, time, and map location
- **CONTRIBUTING.md**: Simplified for open contribution

### Added
- **HTML Reports**: `--html` flag generates shareable HTML reports with embedded CSS
- **Better Context**: Each mistake includes round number, timestamp, and map callout
- **Player Names**: Mistakes now tagged with player name for clarity

### Removed
- COMMERCIAL.md — removed
- Buzzwords: "deterministic auditing", "exploit-resistant", "forensic analysis"

---

## [3.0.1] - License Update (Deprecated)

### Changed
- Internal license updates

## [3.0.0] - 2026-01-12

### 🎮 DEMO PLAYER EDITION

Major release introducing standalone demo playback without CS2 installed.

### Added
- **Demo Player** (`src/player/`) — Visual demo playback with Pygame
  - `python main.py play <demo.dem>` — New CLI command
  - Controls: Space (pause), ←/→ (seek), ↑/↓ (rounds), +/- (speed), 1-9 (jump)
  - Player dots with team colors (CT=blue, T=orange)
  - Kill feed with weapon/headshot indicators
  - HUD with round info, progress bar, tick counter
  - Grid fallback when radar images unavailable

- **Dynamic Tickrate** — Read from demo header (`playback_ticks / playback_time`)
  - Supports 64-tick (MM) and 128-tick (Faceit)
  - No more hardcoded assumptions

- **Performance Optimizations**
  - O(log n) tick lookup via `np.searchsorted` on pre-built index
  - LRU cache (OrderedDict) with 500-entry limit and proper eviction
  - Frame skipping at high playback speeds
  - Delta-time clamped (MAX_DT=0.1) to prevent jumps on focus loss

- **Safe Seek** — Bounds checking + snap to nearest valid tick

### Changed
- **CLI Architecture** — Subcommands: `play`, `analyze`, `check-parsers`
- **ParsedDemo** — Added `tickrate` field to dataclass

### Dependencies
- Added `pygame>=2.5.0`

---

## [2.9.0] - 2026-01-12

### 🚀 PRODUCTION READY RELEASE

### Added
- **Rotator Ceiling**: Maximum rating of 95 for Rotator role (impact multipliers, not stars)
- **Low KDR Soft Cap**: Players with KDR < 0.8 capped at maximum 75 rating
- **Trader Hard Ceiling**: Traders with KDR < 1.0 capped at maximum 80 rating
- **Exit Frag Tax**: Players with 8+ exit frags receive 0.85x rating multiplier
- **Comprehensive TEST_REPORT.txt**: Full documentation of all changes and verification
- **Unit tests** for calibration edge cases

### Changed
- Kill-gate now applied at END of pipeline (after role caps) for maximum effect
- Breakout rule requires KDR > 1.15, KAST > 70%, AND Kills >= 16
- Exit discount uses actual role check instead of swing_score proxy
- Smurf detection now receives real HS% and opening success parameters

### Fixed
- Qlocuu 100→80: Rotator ceiling + Exit tax working
- SaVage 86→75: Low KDR cap working
- hazr 88→80: Trader ceiling working  
- hypex 95→80: Exit frag tax working (13 exits)
- Dycha 98→79: Kill-gate + Trader cap working
- REZ 96→77: KAST breakout guard working

## [2.8.0] - 2026-01-12

### Changed
- **Anchor Breakout Rule**: Now requires KDR > 1.15, KAST > 70%, Kills >= 16
- **Kill-Gate Moved**: Applied after role caps to ensure it reduces final rating
- **Exit Penalty**: Uses role check (Rotator/Trader) instead of swing_score
- **Smurf Detection**: Fixed to pass real HS% and opening success

### Fixed
- REZ SiteAnchor 96→77 (KAST 47% blocked breakout)
- Dycha Trader 98→79 (KAST 68% blocked breakout + kill gate)

## [2.7.0] - 2026-01-12

### Changed
- Entry tax: 0.93x → 0.90x for KDR < 1.0
- Kill-gate: raw > 110/0.95 → raw > 105/0.90
- Exit discount: 2.0 → 3.5 per exit frag over 3
- Breakout KAST guard: 0.65 → 0.70

## [2.6.0] - 2026-01-12

### Added
- Entry KDR < 1.0: 0.93x penalty
- AWPer KDR < 0.9: 0.88x penalty
- Rotator raw < 100: 0.95x penalty
- Kill-gated god rating: raw > 110 + kills < 18

### Changed
- `impact_note` added to JSON meta definitions

## [2.5.0] - 2026-01-12

### Added
- Entry dying tax: 0.93x for KDR < 1.0
- Breakout KAST guard: KAST > 65% required

### Changed
- Kill-gate stricter: 110/0.95 → 105/0.90
- Exit discount harsher: 2.0 → 3.5

## [2.4.0] - 2026-01-12

### Added
- **Floor Clamp**: Minimum rating of 15 (no more zeros)
- **License Added**: MIT
- `team_id` field in PlayerFeatures for proper team assignment

### Changed
- Smurf detection nerfed: 0.85 → 0.92 multiplier, disabled if rounds > 18
- Entry requirements tightened: KAST > 55% + entry_success > 35%
- Exit penalty role-aware: 50% reduced for Rotators

### Fixed
- ztr 0→15: Floor clamp working

## [2.3.0] - 2026-01-12

### Added
- Behavior-based Trader detection (tradeable_ratio > 0.35)
- Behavior-based Rotator detection (swing_kills >= 2)
- Trade bonus for Entry scoring

### Changed
- Lurker threshold: 800u → 650u average teammate distance
- Rotator requires impact >= 30

## [2.2.0] - 2026-01-11

### Added
- Per-team quota enforcement (1 AWPer, 2 Entry per team)
- SiteAnchor/Trader role split by distance
- Role-specific penalties in final rating

### Fixed
- Double AWPer bug on same team
- Support detection with flash requirements

## [2.1.0] - 2026-01-11

### Added
- Role baselines for z-score normalization
- Map difficulty weights
- Dynamic role caps
- WPA diminishing returns (> 2.5 gets halved)
- Soft cap on raw impact at 120

### Changed
- Impact formula rebalanced
- Death penalty increased

## [2.0.0] - 2026-01-11

### Added
- Complete scoring engine rewrite
- Role-based classification system
- Impact score calculation with:
  - Kill value (won/lost rounds)
  - Entry points
  - Clutch points
  - WPA bonus
  - Death penalty
- Aim score with HS%, KPR, ADR
- Positioning score with untradeable ratio
- Utility score with flash/damage tracking

### Infrastructure
- JSON report generation
- Heatmap generation
- Mistake classification
- Drill recommendations
