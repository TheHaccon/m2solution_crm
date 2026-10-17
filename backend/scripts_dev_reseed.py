#!/usr/bin/env python3
"""Local entrypoint; in Docker use: python -m app.seeds"""
from app.seeds.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
