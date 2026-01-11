# Contributing to CS2 AI Coach

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## 🚀 Getting Started

1. **Fork the repository**
2. **Clone your fork**
   ```bash
   git clone https://github.com/YOUR_USERNAME/cs2-ai-coach.git
   cd cs2-ai-coach
   ```
3. **Create a virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

## 📋 Development Guidelines

### Code Style
- Follow PEP 8 guidelines
- Use type hints where possible
- Write docstrings for all functions and classes

### Commit Messages
Use clear, descriptive commit messages:
- `feat: add new positioning metric`
- `fix: handle empty damage dataframe`
- `docs: update README with examples`

### Testing
Before submitting:
```bash
# Test with a demo file
python main.py --demo test.dem --verbose

# Check parser availability
python main.py --check-parsers
```

## 🔧 Areas for Contribution

### High Priority
- [ ] Add more positioning heuristics (cover detection)
- [ ] Improve economy analysis with buy round detection
- [ ] Add more comprehensive tests

### Feature Ideas
- [ ] Web interface for reports
- [ ] Match history tracking
- [ ] Team-level analysis
- [ ] Map-specific coaching

### Documentation
- [ ] Add video tutorials
- [ ] Expand metric explanations
- [ ] Translate to other languages

## 🐛 Reporting Issues

When reporting bugs, include:
1. Python version
2. Operating system
3. Full error traceback
4. Demo file source (HLTV, FACEIT, etc.)

## 📝 Pull Request Process

1. Create a feature branch
2. Make your changes
3. Test thoroughly
4. Update documentation if needed
5. Submit PR with clear description

## 📜 License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Questions? Open an issue or reach out!
