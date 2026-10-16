import argparse
import datetime
import json
import os
import ssl
import sys
import time
import warnings

warnings.filterwarnings("ignore")

import httpx
import yaml

# 停用 SSL 驗證（HKO LiteLLM Proxy 使用內部 CA，容器內無法驗證）
_original_httpx_init = httpx.Client.__init__
def _patched_init(self, *args, **kwargs):
    kwargs.setdefault("verify", False)
    return _original_httpx_init(self, *args, **kwargs)
httpx.Client.__init__ = _patched_init

os.environ.setdefault("SSL_CERT_FILE", "/etc/ssl/certs/ca-certificates.crt")
os.environ.setdefault("REQUESTS_CA_BUNDLE", "/etc/ssl/certs/ca-certificates.crt")

from crewai import Agent, Crew, LLM, Process, Task

from tools import FileWriterTool, GitOpsTool, WebSearchTool


def parse_args():
    parser = argparse.ArgumentParser(
        description="香港建築物導賞手冊 CrewAI 執行腳本"
    )
    parser.add_argument("--building-id", required=True, help="建築物編號")
    parser.add_argument("--category", required=True, help="建築物分類")
    parser.add_argument("--name", required=True, help="建築物中文名稱")
    parser.add_argument("--address", required=True, help="建築物中文地址")
    parser.add_argument("--english-name", default="", help="建築物英文名稱")
    return parser.parse_args()


def load_yaml(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def build_tool_registry():
    return {
        "web_search": WebSearchTool(),
        "file_writer": FileWriterTool(),
        "git_ops": GitOpsTool(),
    }


def build_llm(model_name, config):
    llm_cfg = config.get("llm", {})
    base_url = os.environ.get(
        "HKO_LLM_BASE_URL",
        llm_cfg.get("base_url", "https://litellm.services.hko.gov.hk"),
    )
    api_key = os.environ.get("HKO_API_KEY", "")
    return LLM(
        model=f"openai/{model_name}",
        base_url=base_url,
        api_key=api_key,
        temperature=llm_cfg.get("temperature", 0.7),
        max_tokens=llm_cfg.get("max_tokens", 4096),
    )


def create_agents(agents_config, tool_registry, llm):
    agents = {}
    for key, cfg in agents_config.items():
        tool_names = cfg.get("tools", [])
        tools = [tool_registry[name] for name in tool_names if name in tool_registry]
        agent = Agent(
            role=cfg["role"],
            backstory=cfg["backstory"],
            goal=cfg["goal"],
            verbose=cfg.get("verbose", True),
            allow_delegation=cfg.get("allow_delegation", False),
            tools=tools,
            llm=llm,
        )
        agents[key] = agent
    return agents


def create_tasks(tasks_config, agents):
    tasks = []
    for key, cfg in tasks_config.items():
        agent_key = cfg["agent"]
        agent = agents[agent_key]
        task = Task(
            description=cfg["description"],
            expected_output=cfg["expected_output"],
            agent=agent,
        )
        tasks.append(task)
    return tasks


def get_output_path(category, building_id, name, address):
    category_map = {
        "法定古蹟": "導賞手冊/法定古蹟",
        "新界": "導賞手冊/建築/新界",
        "市區": "導賞手冊/建築/市區",
    }
    base_dir = category_map.get(category)
    if base_dir is None:
        return None
    from tools.file_writer import _sanitize_filename_component
    try:
        building_id = f"{int(building_id):05d}"
    except (ValueError, TypeError):
        pass
    safe_name = _sanitize_filename_component(name)
    safe_address = _sanitize_filename_component(address)
    filename = f"{building_id}-{safe_name}-{safe_address}.md"
    return os.path.join(base_dir, filename)


def fix_markdown_format(file_path, config):
    if not file_path or not os.path.exists(file_path):
        return
    try:
        from openai import OpenAI
    except ImportError:
        return

    ff_cfg = config.get("format_fixer", {})
    base_url = os.environ.get(
        "HKO_LLM_BASE_URL",
        config.get("llm", {}).get("base_url", "https://litellm.services.hko.gov.hk"),
    )
    api_key = os.environ.get("HKO_API_KEY", "")
    model = os.environ.get(
        "HKO_LLM_FALLBACK",
        ff_cfg.get("model", "deepseek-ai/DeepSeek-V4-Flash-0731-Coding"),
    )
    temperature = ff_cfg.get("temperature", 0)
    prompt = ff_cfg.get(
        "prompt",
        "你是 Markdown 格式修復工具。僅修復格式問題，嚴禁新增、刪除或修改任何內容。"
        "修復範圍包括：標題層級、列表縮排、表格對齊、空行、連結語法等。"
        "特別注意表格欄位漂移：若因空值、null 或空字串導致表格欄位錯位，"
        "修復欄位對齊使其與表頭一致，但不得更改任何儲存格的內容。"
        "輸出完整的修復後 Markdown。",
    )

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    client = OpenAI(
        base_url=base_url,
        api_key=api_key,
        http_client=httpx.Client(verify=False),
    )
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": content},
        ],
        temperature=temperature,
    )

    fixed = response.choices[0].message.content
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(fixed)

    format_msg = {
        "status": "format_fixed",
        "file": file_path,
        "model": model,
    }
    print(json.dumps(format_msg, ensure_ascii=False), flush=True)


def make_step_callback(building_id):
    def callback(step):
        agent_name = ""
        if hasattr(step, "agent"):
            agent_name = getattr(step.agent, "role", str(step.agent))
        step_name = type(step).__name__
        message = str(step)
        entry = {
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "agent": agent_name,
            "step": step_name,
            "message": message,
        }
        print(json.dumps(entry, ensure_ascii=False), flush=True)
    return callback


def make_task_callback(building_id, runs_dir):
    def callback(task):
        agent_name = ""
        if hasattr(task, "agent"):
            agent_name = getattr(task.agent, "role", str(task.agent))
        # CrewAI task_callback receives TaskOutput, not Task
        output_text = ""
        if hasattr(task, "raw"):
            output_text = task.raw or ""
        elif hasattr(task, "output") and task.output is not None:
            output_obj = task.output
            if hasattr(output_obj, "raw"):
                output_text = output_obj.raw or ""
            else:
                output_text = str(output_obj)
        state = {
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "building_id": building_id,
            "task": getattr(task, "description", str(task))[:200],
            "agent": agent_name,
            "output": output_text[:5000],
        }
        intermediate_path = os.path.join(runs_dir, "intermediate_research.json")
        existing = []
        if os.path.exists(intermediate_path):
            try:
                with open(intermediate_path, "r", encoding="utf-8") as f:
                    existing = json.load(f)
                    if not isinstance(existing, list):
                        existing = [existing]
            except (json.JSONDecodeError, IOError):
                existing = []
        existing.append(state)
        with open(intermediate_path, "w", encoding="utf-8") as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)
    return callback


def check_credibility_passed(result):
    try:
        if isinstance(result, str):
            data = json.loads(result)
        else:
            data = result
        if isinstance(data, dict):
            if data.get("verdict") == "passed":
                return True
            tasks_output = data.get("tasks_output", [])
            if isinstance(tasks_output, list):
                for item in tasks_output:
                    if isinstance(item, dict) and item.get("verdict") == "passed":
                        return True
        return False
    except (json.JSONDecodeError, TypeError):
        return False


def extract_credibility_verdict(crew_result):
    """從 Crew 結果中提取可信性審查 verdict。"""
    import re

    def try_extract_json(text):
        # 直接 parse
        try:
            return json.loads(text)
        except (json.JSONDecodeError, TypeError):
            pass
        # 從 markdown code block 中提取
        m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(1))
            except json.JSONDecodeError:
                pass
        # 從文字中尋找 JSON 物件
        m = re.search(r'\{[^{}]*"verdict"\s*:\s*"[^"]*"[^{}]*\}', text, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError:
                pass
        return None

    if hasattr(crew_result, "tasks_output"):
        for task_output in crew_result.tasks_output:
            raw = str(task_output)
            parsed = try_extract_json(raw)
            if parsed and isinstance(parsed, dict):
                v = parsed.get("verdict", "")
                if v in ("passed", "failed"):
                    return v
    if isinstance(crew_result, str):
        parsed = try_extract_json(crew_result)
        if parsed and isinstance(parsed, dict):
            return parsed.get("verdict", "failed")
    # fallback: 搜尋 "passed" 字樣
    text = str(crew_result)
    if '"verdict"' in text and '"passed"' in text:
        return "passed"
    return "failed"


def main():
    args = parse_args()
    building_id = args.building_id

    script_dir = os.path.dirname(os.path.abspath(__file__))
    agents_config = load_yaml(os.path.join(script_dir, "agents.yaml"))
    tasks_config = load_yaml(os.path.join(script_dir, "tasks.yaml"))
    config = load_yaml(os.path.join(script_dir, "config.yaml"))

    runs_dir = os.path.join(script_dir, "runs", building_id)
    os.makedirs(runs_dir, exist_ok=True)

    tool_registry = build_tool_registry()

    retry_cfg = config.get("retry", {})
    max_attempts = retry_cfg.get("max_attempts", 3)
    backoff_seconds = retry_cfg.get("backoff_seconds", 5)
    fallback_from_attempt = retry_cfg.get("fallback_from_attempt", 3)

    primary_model = os.environ.get(
        "HKO_LLM_PRIMARY",
        config.get("llm", {}).get("primary_model", "zai-org/GLM-5.2-FP8"),
    )
    fallback_model = os.environ.get(
        "HKO_LLM_FALLBACK",
        config.get("llm", {}).get(
            "fallback_model", "deepseek-ai/DeepSeek-V4-Flash-0731-Coding"
        ),
    )

    step_callback = make_step_callback(building_id)
    task_callback = make_task_callback(building_id, runs_dir)

    crew_config = config.get("crew", {})

    last_error = None
    for attempt in range(1, max_attempts + 1):
        model_name = (
            primary_model if attempt < fallback_from_attempt else fallback_model
        )
        llm = build_llm(model_name, config)

        agents = create_agents(agents_config, tool_registry, llm)
        tasks = create_tasks(tasks_config, agents)

        crew = Crew(
            agents=list(agents.values()),
            tasks=tasks,
            process=Process.sequential,
            verbose=crew_config.get("verbose", True),
            memory=crew_config.get("memory", True),
            max_rpm=crew_config.get("max_rpm", 10),
            step_callback=step_callback,
            task_callback=task_callback,
        )

        attempt_msg = {
            "status": "attempt",
            "building_id": building_id,
            "attempt": attempt,
            "model": model_name,
        }
        print(json.dumps(attempt_msg, ensure_ascii=False), flush=True)

        try:
            result = crew.kickoff(
                inputs={
                    "building_id": args.building_id,
                    "category": args.category,
                    "name": args.name,
                    "address": args.address,
                    "english_name": args.english_name,
                }
            )
            verdict = extract_credibility_verdict(result)
            if verdict == "passed":
                output_path = get_output_path(
                    args.category, args.building_id, args.name, args.address
                )
                fix_markdown_format(output_path, config)

                final_state = {
                    "building_id": building_id,
                    "category": args.category,
                    "name": args.name,
                    "address": args.address,
                    "english_name": args.english_name,
                    "status": "passed",
                    "attempts": attempt,
                    "model": model_name,
                    "verdict": verdict,
                    "timestamp": datetime.datetime.now(
                        datetime.timezone.utc
                    ).isoformat(),
                    "result": str(result),
                }
                intermediate_path = os.path.join(
                    runs_dir, "intermediate_research.json"
                )
                with open(intermediate_path, "w", encoding="utf-8") as f:
                    json.dump(final_state, f, ensure_ascii=False, indent=2)
                success_msg = {
                    "status": "success",
                    "building_id": building_id,
                    "verdict": "passed",
                    "attempts": attempt,
                    "model": model_name,
                }
                print(json.dumps(success_msg, ensure_ascii=False), flush=True)
                sys.exit(0)
            else:
                last_error = (
                    f"第 {attempt} 次嘗試（模型：{model_name}）："
                    f"可信性審查未通過（verdict={verdict}）"
                )
                if attempt < max_attempts:
                    time.sleep(backoff_seconds)
        except Exception as exc:
            last_error = (
                f"第 {attempt} 次嘗試（模型：{model_name}）發生例外：{str(exc)}"
            )
            if attempt < max_attempts:
                time.sleep(backoff_seconds)

    exception_log = {
        "building_id": building_id,
        "category": args.category,
        "name": args.name,
        "address": args.address,
        "english_name": args.english_name,
        "status": "failed",
        "max_attempts": max_attempts,
        "error": last_error,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    exception_path = os.path.join(runs_dir, "exception_log.json")
    with open(exception_path, "w", encoding="utf-8") as f:
        json.dump(exception_log, f, ensure_ascii=False, indent=2)

    error_msg = {
        "status": "error",
        "building_id": building_id,
        "error": last_error,
        "attempts": max_attempts,
    }
    print(json.dumps(error_msg, ensure_ascii=False), flush=True)
    sys.exit(1)


if __name__ == "__main__":
    main()
