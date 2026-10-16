#!/usr/bin/env python3
"""PM 包裝腳本：關閉建築物 GitHub Issue（成功或跳過）。僅接收 building_id + action。"""
import subprocess
import sys


def main():
    bid = sys.argv[1]
    action = sys.argv[2] if len(sys.argv) > 2 else "completed"
    category = sys.argv[3] if len(sys.argv) > 3 else None

    try:
        bid = f"{int(bid):05d}"
    except (ValueError, TypeError):
        bid = str(bid)

    if category:
        search = f"建築物 {category} {bid}："
    else:
        search = f"建築物 {bid}："
    try:
        result = subprocess.run(
            ["gh", "issue", "list", "--repo", "Mcc-Mak/hk-tour-guide-n8n",
             "--search", search, "--state", "open",
             "--json", "number", "--limit", "1", "-q", ".[0].number"],
            capture_output=True, text=True, timeout=15,
        )
        issue_num = result.stdout.strip()
        if issue_num:
            if action == "completed":
                comment = f"✅ 建築物 {bid} 導賞手冊已完成。"
                reason_args = []
            else:
                comment = f"⏭️ 建築物 {bid} 硬關卡未通過，已跳過。"
                reason_args = ["--reason", "not_planned"]

            subprocess.run(
                ["gh", "issue", "close", issue_num,
                 "--repo", "Mcc-Mak/hk-tour-guide-n8n",
                 "--comment", comment] + reason_args,
                capture_output=True, text=True, timeout=15,
            )

            try:
                subprocess.run(
                    ["gh", "project", "item-add", "11", "--owner", "Mcc-Mak",
                     "--url", f"https://github.com/Mcc-Mak/hk-tour-guide-n8n/issues/{issue_num}"],
                    capture_output=True, text=True, timeout=15,
                )
            except Exception:
                pass

            print(f"PM_DONE:{bid}:{action}")
        else:
            print(f"NO_ISSUE:{bid}")
    except Exception as e:
        print(f"PM_ERR:{bid}:{e}")


if __name__ == "__main__":
    main()
