# Contributing to FragAudit

Contributions welcome. This project is MIT licensed.

---

## How to Contribute

1. Fork the repo
2. Create a branch: `git checkout -b fix/your-fix`
3. Make your changes
4. Run tests: `python -m pytest tests/ -v`
5. Commit: `git commit -m "fix: description"`
6. Push and open a PR

---

## What We Accept

- Bug fixes with tests
- New detection rules (with clear rationale)
- Documentation improvements
- Performance improvements
- Demo player enhancements

---

## What We Don't Accept

- Cosmetic-only changes
- Breaking changes without discussion
- Features without tests
- Code without clear purpose

---

## Code Style

- Python 3.11+
- Type hints where useful
- Docstrings for public functions
- Keep functions focused

---

## Commit Messages

Use conventional commits:

```
fix: correct dry peek detection threshold
feat: add flash support detection
docs: update README examples
test: add edge case for clutch detection
```

---

## Testing

```bash
python -m pytest tests/ -v
```

All tests must pass before merging.

---

## Questions?

Open an issue. Keep it focused.
