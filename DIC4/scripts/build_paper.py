#!/usr/bin/env python3
"""Build the IEEE draft using a configured local TeX distribution."""
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper"

def run(command):
    subprocess.run(command, cwd=PAPER, check=True)

def main():
    if shutil.which("latexmk"):
        run(["latexmk", "-pdf", "-interaction=nonstopmode", "-halt-on-error", "main.tex"])
    elif shutil.which("pdflatex") and shutil.which("bibtex"):
        command = ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", "main.tex"]
        run(command)
        run(["bibtex", "main"])
        run(command)
        run(command)
    else:
        raise SystemExit("Install/configure TeX Live or MiKTeX, or import the provided ZIP into Overleaf.")
    if not (PAPER / "main.pdf").is_file():
        raise SystemExit("Build finished without main.pdf")
    print(f"Built: {PAPER / 'main.pdf'}")

if __name__ == "__main__":
    main()
