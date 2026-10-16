#!/usr/bin/env python3
"""更新建築矩陣.md：將指定建築物標記為已完成並填入歷史檔案連結。"""
import re
import sys


def sanitize(t):
    t = re.sub(r"[（(].*?[）)]", "", t)
    t = re.sub(r'[/\\:*?"<>|]', "", t)
    t = t.strip().strip(".")
    t = re.sub(r"\s+", "", t)
    return t if t else "未知"


def main():
    bid = sys.argv[1]
    name = sys.argv[2]
    addr = sys.argv[3]
    category = sys.argv[4]

    cat_map = {
        "法定古蹟": "導賞手冊/法定古蹟",
        "新界": "導賞手冊/建築/新界",
        "市區": "導賞手冊/建築/市區",
    }
    base = cat_map.get(category, "導賞手冊/法定古蹟")
    safe_name = sanitize(name)
    safe_addr = sanitize(addr)
    try:
        bid = f"{int(bid):05d}"
    except (ValueError, TypeError):
        pass
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
