# Changelog

All notable changes to CS2 AI Coach will be documented in this file.

## [1.0.0] - 2026-01-11

### Added
- Initial release
- Demo parsing with demoparser2
- Feature extraction (aim, positioning, utility, economy)
- Rule-based mistake classification with confidence scores
- Optional Ollama NLP integration for AI coaching feedback
- JSON and Markdown report generation
- CLI with `--demo`, `--ollama`, `--markdown`, `--verbose` options
- Verified working on pro match demos (fl0m Mythical LAN)

### Technical
- Modular architecture with separate parser, metrics, classifier, and report modules
- Fallback messages when Ollama is unavailable
- Type-safe DataFrame handling
- Comprehensive examples and documentation
