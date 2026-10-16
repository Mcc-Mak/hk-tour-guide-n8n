#!/usr/bin/env python3
"""PM 包裝腳本：建立建築物 GitHub Issue。僅接收 building_id。"""
import json
import re
import subprocess
import sys


def lookup_building(bid, category=None):
    try:
        bid = f"{int(bid):05d}"
    except (ValueError, TypeError):
        bid = str(bid)
    with open("建築矩陣.md", "r", encoding="utf-8") as f:
        content = f.read()
    section_map = {"法定古蹟": "法定古蹟", "市區": "市區", "新界": "新界"}
    for section in re.split(r"^(?=### )", content, flags=re.MULTILINE):
        m = re.match(r"^### (.+)", section)
        if not m:
            continue
        cat = section_map.get(m[1].strip())
        if not cat or (category and cat != category):
            continue
        for line in section.split("\n"):
            line = line.strip()
            if not line.startswith("|") or "---" in line or "編號" in line:
                continue
            cells = line.split("|")
            cells.pop(0)
            cells.pop()
            if len(cells) < 10:
                continue
            if cells[0].strip() == bid:
                return {
                    "building_id": bid,
                    "category": cat,
                    "chinese_name": cells[2].strip(),
                    "english_name": cells[3].strip(),
                    "chinese_address": cells[4].strip(),
                }
    return None


def main():
    bid = sys.argv[1]
    category = sys.argv[2] if len(sys.argv) > 2 else None
    info = lookup_building(bid, category)
    if not info:
        print(f"NOT_FOUND:{bid}")
        return
    title = f"建築物 {info['category']} {info['building_id']}：{info['chinese_name']}"
    body = (
        f"## 建築物資訊\n"
        f"- 編號：{info['building_id']}\n"
        f"- 中文名稱：{info['chinese_name']}\n"
        f"- 英文名稱：{info['english_name']}\n"
        f"- 中文地址：{info['chinese_address']}\n"
        f"- 分類：{info['category']}\n"
        f"\n## 狀態\n"
        f"- [ ] CrewAI 歷史研究\n"
        f"- [ ] 硬關卡審查\n"
        f"- [ ] 導賞手冊產出\n"
        f"- [ ] Git 提交推送\n"
    )
    try:
        result = subprocess.run(
            ["gh", "issue", "create", "--repo", "Mcc-Mak/hk-tour-guide-n8n",
             "--title", title, "--body", body, "--label", "building"],
            capture_output=True, text=True, timeout=15,
        )
        if result.returncode == 0:
            print(f"ISSUE_CREATED:{result.stdout.strip()}")
        else:
            print(f"ISSUE_EXISTS:{bid}")
    except Exception:
        print(f"ISSUE_EXISTS:{bid}")


if __name__ == "__main__":
    main()
