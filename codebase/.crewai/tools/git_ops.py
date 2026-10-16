import shlex
import subprocess

try:
    from crewai.tools import BaseTool
except ImportError:
    from crewai_tools.tools import BaseTool


class GitOpsTool(BaseTool):
    name: str = "git_ops"
    description: str = (
        "Stage files, commit, and push to dev-001 branch"
    )

    def _run(self, file_paths: str, commit_message: str) -> str:
        results = []
        try:
            add_cmd = ["git", "add"] + [
                p.strip() for p in file_paths.split(",") if p.strip()
            ]
            subprocess.run(add_cmd, check=True, capture_output=True, text=True)
            results.append("git add 成功")

            commit_cmd = ["git", "commit", "-m", commit_message]
            subprocess.run(
                commit_cmd, check=True, capture_output=True, text=True
            )
            results.append("git commit 成功")

            push_cmd = ["git", "push", "origin", "dev-001"]
            subprocess.run(push_cmd, check=True, capture_output=True, text=True)
            results.append("git push origin dev-001 成功")

            return "；".join(results)
        except subprocess.CalledProcessError as exc:
            stderr = exc.stderr or ""
            return f"git 操作失敗：{stderr}"
        except Exception as exc:
            return f"git 操作失敗：{str(exc)}"
