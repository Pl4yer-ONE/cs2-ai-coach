#!/usr/bin/env python3
"""
FragAudit Desktop UI
Run this to launch the graphical interface.

Usage:
    python run_ui.py
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.ui.app import FragAuditApp


def main():
    """Launch the FragAudit desktop application."""
    app = FragAuditApp()
    app.run()


if __name__ == "__main__":
    main()
