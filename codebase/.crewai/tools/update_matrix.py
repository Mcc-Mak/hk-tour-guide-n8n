#!/usr/bin/env python3
"""更新建築矩陣.md：將指定建築物標記為已完成並填入歷史檔案連結。
僅接收 building_id 與 category，自行從矩陣查詢名稱與地址。
"""
import re
import sys


def sanitize(t):
    t = re.sub(r"[（(].*?[）)]", "", t)
    t = re.sub(r'[/\\:*?"<>|]', "", t)
    t = t.strip().strip(".")
    t = re.sub(r"\s+", "", t)
    return t if t else "未知"


def lookup_building(bid, category):
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
                    "chinese_address": cells[4].strip(),
                }
    return None


def main():
    if len(sys.argv) < 2:
        print("用法: update_matrix.py <building_id> [category]")
        sys.exit(1)
    bid = sys.argv[1]
    category = sys.argv[2] if len(sys.argv) > 2 else None

    info = lookup_building(bid, category)
    if not info:
        print(f"NOT_FOUND:{bid}:{category or 'ALL'}")
        return

    bid = info["building_id"]
    name = info["chinese_name"]
    addr = info["chinese_address"]
    cat = info["category"]

    cat_map = {
        "法定古蹟": "導賞手冊/法定古蹟",
        "新界": "導賞手冊/建築/新界",
        "市區": "導賞手冊/建築/市區",
    }
    base = cat_map.get(cat, "導賞手冊/法定古蹟")
    safe_name = sanitize(name)
    safe_addr = sanitize(addr)
    link = f"{base}/{bid}-{safe_name}-{safe_addr}.md"

    with open("建築矩陣.md", "r", encoding="utf-8") as f:
        content = f.read()

    pattern = (
        rf'(\| {bid} \|[^|]+\| {re.escape(name)} \|.*?)'
        r'🌚 未開始 \| \*\(由 CrewAI 動態產出 Markdown 連結\)\* \|'
    )
    replacement = rf'\1🌕 已完成 | [`歷史檔案（連結）`]({link}) |'

    new_content, count = re.subn(pattern, replacement, content)

    if count > 0:
        with open("建築矩陣.md", "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"已更新 {count} 行：建築物 {bid} {name}")
    else:
        print(f"未找到匹配行：建築物 {bid} {name}（可能已標記為已完成）")


if __name__ == "__main__":
    main()
