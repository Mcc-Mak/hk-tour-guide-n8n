import json
import os

import requests

try:
    from crewai.tools import BaseTool
except ImportError:
    from crewai_tools.tools import BaseTool


class WebSearchTool(BaseTool):
    name: str = "web_search"
    description: str = (
        "Search the web for Hong Kong building historical information"
    )

    def _run(self, query: str) -> str:
        api_key = os.environ.get("SEARCH_API_KEY", "")
        endpoint = os.environ.get(
            "SEARCH_API_ENDPOINT",
            "https://www.googleapis.com/customsearch/v1",
        )
        params = {
            "key": api_key,
            "q": query,
            "num": 10,
        }
        try:
            response = requests.get(endpoint, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            results = []
            items = data.get("items", [])
            for item in items:
                results.append(
                    {
                        "title": item.get("title", ""),
                        "url": item.get("link", ""),
                        "snippet": item.get("snippet", ""),
                    }
                )
            return json.dumps(results, ensure_ascii=False)
        except Exception as exc:
            return json.dumps(
                {"error": str(exc)}, ensure_ascii=False
            )
