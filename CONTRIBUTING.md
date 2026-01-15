# Contributing to FragAudit

Thank you for your interest in contributing! This guide will help you get started.

---

## Ways to Contribute

### 🐛 Report Bugs
Found an issue? [Open a bug report](https://github.com/Pl4yer-ONE/FragAudit/issues/new?template=bug_report.md)

### 💡 Suggest Features
Have an idea? [Open a feature request](https://github.com/Pl4yer-ONE/FragAudit/issues/new?template=feature_request.md)

### 📊 Share Analysis
Found interesting patterns? Share in [Discussions](https://github.com/Pl4yer-ONE/FragAudit/discussions)

### 🛠️ Submit Code
Fix bugs or add features. See below for setup.

---

## Good First Issues

Looking for your first contribution? Try these:

| Label | Description |
|-------|-------------|
| `good first issue` | Simple, self-contained tasks |
| `documentation` | Improve docs or examples |
| `tests` | Add test coverage |

---

## Development Setup

```bash
# 1. Fork and clone
git clone https://github.com/YOUR_USERNAME/FragAudit.git
cd FragAudit

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # If available

# 4. Run tests
python -m pytest tests/ -v
```

---

## Code Standards

### Python Style
- Follow PEP 8
- Use type hints where possible
- Keep functions under 50 lines

### Commit Messages
```
type: short description

- feat: New feature
- fix: Bug fix
- docs: Documentation
- test: Tests
- perf: Performance
- refactor: Code refactor
```

Example:
```
feat: Add flash assist tracking to role classifier

- Track flash_assists per player
- Add to Support role detection criteria
- Update tests
```

### Testing
- All new features need tests
- Run full suite before PR: `pytest tests/`
- Maintain 100% pass rate

---

## Pull Request Process

1. **Fork** the repository
2. **Create a branch**: `git checkout -b feature/your-feature`
3. **Make changes** and commit
4. **Run tests**: `pytest tests/`
5. **Push**: `git push origin feature/your-feature`
6. **Open PR** with clear description

### PR Checklist
- [ ] Tests pass (`pytest tests/`)
- [ ] Code follows style guide
- [ ] Commit messages are clear
- [ ] Documentation updated (if needed)

---

## Example Contributions

### Adding a New Mistake Type

1. Edit `src/mistakes/detectors.py`
2. Add detection logic
3. Add tests in `tests/test_mistakes.py`
4. Update `docs/` if needed

```python
# Example: Adding "FLASH_PEEK" mistake type
class MistakeDetector:
    def detect_flash_peek(self, kill_event):
        """Detect when player peeks while flashed."""
        if kill_event.victim_was_flashed:
            return Mistake(
                type=MistakeType.FLASH_PEEK,
                severity=Severity.MEDIUM,
                description="Peeked while flashed"
            )
```

### Adding a New Role

1. Edit `src/roles/classifier.py`
2. Define detection criteria
3. Add tests in `tests/test_roles.py`

```python
# Example: Adding "AGGRO_CT" role
def classify_aggro_ct(features):
    """Detect aggressive CT play."""
    if features.t_side_kills >= 3 and features.avg_distance > 500:
        return Role.AGGRO_CT, 0.7
```

---

## Questions?

- [GitHub Discussions](https://github.com/Pl4yer-ONE/FragAudit/discussions) for questions
- [Issues](https://github.com/Pl4yer-ONE/FragAudit/issues) for bugs/features

---

## License

By contributing, you agree that your contributions will be licensed under the **GNU General Public License v3.0**.
