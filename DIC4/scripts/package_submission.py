#!/usr/bin/env python3
"""Package the compiled paper, Overleaf sources, and complete DIC4 project."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import zipfile


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    out = args.output_dir.resolve()
    if out == root or root in out.parents:
        parser.error("Use an output directory outside the project to avoid recursive packaging.")
    out.mkdir(parents=True, exist_ok=True)
    pdf = root / "paper/main.pdf"
    if not pdf.is_file():
        parser.error("Compile paper/main.pdf before packaging.")

    excluded_parts = {".git", "node_modules", "__pycache__", ".venv"}
    excluded_suffixes = {".pyc", ".aux", ".out", ".toc", ".fls", ".fdb_latexmk"}
    files = sorted(p for p in root.rglob("*") if p.is_file()
                   and not (set(p.relative_to(root).parts) & excluded_parts)
                   and p.suffix not in excluded_suffixes
                   and p.name != "FILE_MANIFEST.json")
    manifest = {
        "scope": "Hashes of the packaged project files; the manifest excludes itself.",
        "files": [{"path": p.relative_to(root).as_posix(),
                   "bytes": p.stat().st_size, "sha256": sha256(p)} for p in files],
    }
    manifest_path = root / "FILE_MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    files.append(manifest_path)

    paper_out = out / "Traffic_Assistant_DIC4_Paper.pdf"
    shutil.copy2(pdf, paper_out)
    overleaf_out = out / "Traffic_Assistant_DIC4_Overleaf.zip"
    overleaf_sources = ["main.tex", "references.bib", "IEEEtran.cls", "IEEEtran.bst",
                        "figures/architecture.pdf", "figures/scenario_changes.pdf"]
    with zipfile.ZipFile(overleaf_out, "w", zipfile.ZIP_DEFLATED) as archive:
        for relative in overleaf_sources:
            archive.write(root / "paper" / relative, relative)

    submission_out = out / "Traffic_Assistant_DIC4_Submission.zip"
    start = """# DIC4 交通配時助手：先讀這裡

1. Traffic_Assistant_DIC4_Paper.pdf：5 頁英文 IEEE 研討會草稿。
2. Traffic_Assistant_DIC4_Overleaf.zip：直接在 Overleaf 選 Upload Project 匯入。
3. traffic-assistant-dic4/：完整 GitHub 專案，包含 OpenSpec、MCP、程式來源與真實查核紀錄。

作者欄已依本人提供的正式英文姓名設為 Po Sheng Wei。
詳細指引：traffic-assistant-dic4/docs/SUBMISSION_GUIDE.md。
本次進度：traffic-assistant-dic4/latest.md。
實際線上發布狀態：traffic-assistant-dic4/docs/PUBLICATION_STATUS.json。
產生檔案不代表已在 Overleaf、GitHub 發布，也不代表已在課程平台繳交。
截圖截止日期：2026-11-28；截圖未顯示時分。
"""
    with zipfile.ZipFile(submission_out, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("START_HERE.md", start)
        archive.write(paper_out, paper_out.name)
        archive.write(overleaf_out, overleaf_out.name)
        for path in files:
            archive.write(path, "traffic-assistant-dic4/" + path.relative_to(root).as_posix())
    for path in (overleaf_out, submission_out):
        with zipfile.ZipFile(path) as archive:
            bad = archive.testzip()
            if bad is not None:
                raise RuntimeError(f"Archive integrity error: {bad}")
    for path in (paper_out, overleaf_out, submission_out):
        print(json.dumps({"path": str(path), "bytes": path.stat().st_size,
                          "sha256": sha256(path)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
