import re
from dataclasses import dataclass
from pathlib import Path

TASK_PATTERN = re.compile(r"^- \[([ x])\] (.+?)(?:\s+#task)\s*$")


@dataclass
class Task:
    text: str
    completed: bool
    file: Path
    line: int


def scan_tasks(vault_path: Path) -> list[Task]:
    tasks = []
    for md_file in sorted(vault_path.rglob("*.md")):
        lines = md_file.read_text().splitlines()
        for i, line in enumerate(lines, start=1):
            match = TASK_PATTERN.match(line)
            if match:
                completed = match.group(1) == "x"
                text = match.group(2).strip()
                tasks.append(Task(text=text, completed=completed, file=md_file, line=i))
    return tasks


def toggle_task(file: Path, line: int) -> None:
    lines = file.read_text().splitlines()
    idx = line - 1
    if idx < 0 or idx >= len(lines):
        return
    if "- [ ]" in lines[idx]:
        lines[idx] = lines[idx].replace("- [ ]", "- [x]", 1)
    elif "- [x]" in lines[idx]:
        lines[idx] = lines[idx].replace("- [x]", "- [ ]", 1)
    file.write_text("\n".join(lines) + "\n")


def add_task(file: Path, text: str) -> None:
    if file.exists():
        content = file.read_text()
        if not content.endswith("\n"):
            content += "\n"
        content += f"- [ ] {text} #task\n"
    else:
        content = f"- [ ] {text} #task\n"
    file.write_text(content)
