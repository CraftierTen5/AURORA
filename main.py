"""
AURORA — Airport Runway & Operations Management
Desktop application entry point
Runs the Pygame Desktop Application.
"""

import os
import sys

# Establish DPI awareness before pygame/SDL is imported. Otherwise Windows may
# bitmap-scale the fixed-size Pygame window and make text look blurred.
if sys.platform == "win32":
    os.environ.setdefault("SDL_WINDOWS_DPI_AWARENESS", "permonitorv2")
    try:
        import ctypes
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except (AttributeError, OSError):
            ctypes.windll.user32.SetProcessDPIAware()
    except (AttributeError, OSError):
        pass

def check_environment():
    """Validates runtime prerequisites and reports helpful hints."""
    missing = []
    try:
        import pygame
    except ImportError:
        missing.append("pygame (install via: pip install pygame)")

    has_mysql = False
    try:
        import mysql.connector
        has_mysql = True
    except ImportError:
        pass

    try:
        import pymysql
        has_mysql = True
    except ImportError:
        pass

    if not has_mysql:
        missing.append("mysql-connector-python or pymysql (install via: pip install mysql-connector-python)")

    if missing:
        print("=" * 60)
        print("  AURORA Prerequisite Check: Missing Packages")
        print("=" * 60)
        for m in missing:
            print(f"  [-] {m}")
        print("\nPlease run: pip install -r requirements.txt")
        print("=" * 60)
        return False
    return True

def main():
    if not check_environment():
        sys.exit(1)

    from app import AuroraApp
    app = AuroraApp()
    app.run()

if __name__ == "__main__":
    main()
