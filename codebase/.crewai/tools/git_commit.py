#!/usr/bin/env python3
"""標準化 Git 提交腳本：繁體中文提交訊息 + 語意化 stage。

接收 building_id 與 category，從建築矩陣查詢建築物資訊，
生成標準化提交訊息並提交推送至 dev-001。

用法: git_commit.py <building_id> <category>
"""
import json
import os
import re
import subprocess
import sys


def lookup_building(bid, category=None):
    try:
        bid = f"{int(bid):05d}"
    except (ValueError, TypeError):
        bid = str(bid)
    matrix_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "建築矩陣.md",
    )
    with open(matrix_path, "r", encoding="utf-8") as f:
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


def run(cmd, cwd="/data/codebase"):
    env = os.environ.copy()
    env["GIT_DISCOVERY_ACROSS_FILESYSTEM"] = "1"
    r = subprocess.run(
        cmd, shell=True, cwd=cwd, capture_output=True, text=True, env=env
    )
    return r.returncode, r.stdout, r.stderr


def main():
    if len(sys.argv) < 2:
        print("用法: git_commit.py <building_id> <category>")
        sys.exit(1)
    bid = sys.argv[1]
    category = sys.argv[2] if len(sys.argv) > 2 else None

    info = lookup_building(bid, category)
    if not info:
        print(f"NOT_FOUND:{bid}:{category or 'ALL'}")
        sys.exit(1)

    bid = info["building_id"]
    name = info["chinese_name"]
    cat = info["category"]

    category_map = {
        "法定古蹟": "法定古蹟",
        "新界": "建築/新界",
        "市區": "建築/市區",
    }
    output_base = category_map.get(cat, "法定古蹟")

    steps = []
    # 1. Stage files
    rc, out, err = run(
        f'git add "導賞手冊/" "建築矩陣.md" "../CHANGELOG" ".crewai/runs/"'
    )
    steps.append(f"git add: rc={rc}")
    if rc != 0:
        print(json.dumps({"status": "error", "step": "git_add", "stderr": err}, ensure_ascii=False))
        sys.exit(1)

    # 2. Commit with standardized Traditional Chinese message
    subject = f"docs(tour): 生成 [{bid}] {name} 導賞手冊"
    body = (
        f"建築名稱：{name}\n"
        f"檔案路徑：codebase/導賞手冊/{output_base}/{bid}-*.md\n"
        f"矩陣編號：{bid}\n"
        f"可信性等級：種子\n"
        f"結構：六段式標準章節 + CL 評級表 + 動態歷史檔案連結\n"
        f"矩陣狀態：🌕 已完成"
    )
    commit_msg = f"{subject}\n\n{body}"
    rc, out, err = run(f'git commit -m "{subject}" -m "{body}"')
    steps.append(f"git commit: rc={rc}")
    if rc != 0 and "nothing to commit" not in err and "nothing to commit" not in out:
        print(json.dumps({"status": "error", "step": "git_commit", "stdout": out, "stderr": err}, ensure_ascii=False))
        sys.exit(1)

    # 3. Push to dev-001
    rc, out, err = run("git push origin dev-001")
    steps.append(f"git push: rc={rc}")
    if rc != 0:
        print(json.dumps({"status": "error", "step": "git_push", "stdout": out, "stderr": err}, ensure_ascii=False))
        sys.exit(1)

    result = {
        "status": "committed",
        "building_id": bid,
        "name": name,
        "subject": subject,
    }
    print(json.dumps(result, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
