import re
from dataclasses import dataclass
from pathlib import Path

CHECKBOX_PATTERN = re.compile(r"^- \[([ x])\] (.+)$")


@dataclass
class Task:
    text: str
    completed: bool
    file: Path
    line: int


def _extract_task_text(raw: str) -> str | None:
    """Return task text if line contains #task anywhere, else None."""
    if "#task" not in raw:
        return None
    text = re.sub(r"#task\b", "", raw).strip()
    # Remove trailing metadata like ✅ 2026-04-20
    text = re.sub(r"\s*✅\s*\d{4}-\d{2}-\d{2}\s*$", "", text)
    return text


def scan_tasks(vault_path: Path) -> list[Task]:
    tasks = []
    for md_file in sorted(vault_path.rglob("*.md")):
        try:
            lines = md_file.read_text().splitlines()
        except (UnicodeDecodeError, OSError):
            continue
        for i, line in enumerate(lines, start=1):
            match = CHECKBOX_PATTERN.match(line)
            if match:
                completed = match.group(1) == "x"
                raw_text = match.group(2)
                text = _extract_task_text(raw_text)
                if text is not None:
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
