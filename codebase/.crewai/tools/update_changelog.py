#!/usr/bin/env python3
"""CHANGELOG 更新腳本：追加建築物紀錄。僅接收 building_id。"""
import os
import re
import sys
from datetime import date


def find_changelog():
    """在 CWD、上層目錄搜尋 CHANGELOG 檔案。"""
    candidates = [
        "CHANGELOG",
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__)))), "CHANGELOG"),
        "../CHANGELOG",
    ]
    for path in candidates:
        if os.path.isfile(path):
            return path
    return "CHANGELOG"


def main():
    if len(sys.argv) < 2:
        print("用法: update_changelog.py <building_id>")
        sys.exit(1)
    bid = sys.argv[1]
    try:
        bid = f"{int(bid):05d}"
    except (ValueError, TypeError):
        bid = str(bid)

    changelog_path = find_changelog()

    with open(changelog_path, "r", encoding="utf-8") as f:
        content = f.read()

    m = re.search(r"## \[(\d+)\.(\d+)\.(\d+)\]", content)
    if m:
        major, minor, patch = int(m[1]), int(m[2]), int(m[3]) + 1
    else:
        major, minor, patch = 0, 0, 1

    ver = f"{major}.{minor}.{patch}"
    today = date.today().isoformat()
    entry = (
        f"## [{ver}] - {today}\n\n"
        f"### Added\n\n"
        f"- docs(tour): 生成 [{bid}] 導賞手冊\n\n"
    )
    with open(changelog_path, "w", encoding="utf-8") as f:
        f.write(entry + content)
    print(f"CHANGELOG_UPDATED:{ver}")


if __name__ == "__main__":
    main()
