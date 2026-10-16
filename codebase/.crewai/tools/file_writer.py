import os
import re

try:
    from crewai.tools import BaseTool
except ImportError:
    from crewai_tools.tools import BaseTool


def _sanitize_filename_component(text: str) -> str:
    """將文字轉為 Linux 檔名安全字串：移除括號、斜線、空格等不安全字元。"""
    if not text:
        return "未知"
    # 移除全形與半形括號及其內容
    text = re.sub(r"[（(].*?[）)]", "", text)
    # 移除路徑分隔符與不安全字元
    text = re.sub(r'[/\\:*?"<>|]', "", text)
    # 移除前後空白與句點
    text = text.strip().strip(".")
    # 將連續空白壓縮為單一空格後移除
    text = re.sub(r"\s+", "", text)
    return text if text else "未知"


class FileWriterTool(BaseTool):
    name: str = "file_writer"
    description: str = (
        "依據建築物分類將 Markdown 導賞手冊寫入正確路徑，"
        "檔名格式：{NNNNN}-{中文名稱}-{中文地址}.md"
    )

    def _run(
        self,
        content: str,
        building_id: str,
        category: str,
        name: str,
        address: str,
    ) -> str:
        category_map = {
            "法定古蹟": "導賞手冊/法定古蹟",
            "新界": "導賞手冊/建築/新界",
            "市區": "導賞手冊/建築/市區",
        }
        base_dir = category_map.get(category)
        if base_dir is None:
            return f"錯誤：未知分類「{category}」"
        os.makedirs(base_dir, exist_ok=True)

        # 確保 building_id 為 5 位數零填充格式
        try:
            building_id = f"{int(building_id):05d}"
        except (ValueError, TypeError):
            pass

        # 清理名稱與地址為 Linux 檔名安全字串
        safe_name = _sanitize_filename_component(name)
        safe_address = _sanitize_filename_component(address)
        filename = f"{building_id}-{safe_name}-{safe_address}.md"
        file_path = os.path.join(base_dir, filename)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return file_path
