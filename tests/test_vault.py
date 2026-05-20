from app.services.vault import scan_tasks, toggle_task, add_task


def test_scan_finds_incomplete_tasks(tmp_path):
    note = tmp_path / "2026-05-19.md"
    note.write_text(
        "# Today\n- [ ] Buy groceries #task\n- [x] Call dentist #task\n- Regular note\n"
    )
    tasks = scan_tasks(tmp_path)
    incomplete = [t for t in tasks if not t.completed]
    assert len(incomplete) == 1
    assert incomplete[0].text == "Buy groceries"
    assert incomplete[0].file == note
    assert incomplete[0].line == 2


def test_scan_finds_tasks_across_files(tmp_path):
    (tmp_path / "a.md").write_text("- [ ] Task A #task\n")
    (tmp_path / "b.md").write_text("- [ ] Task B #task\n")
    tasks = scan_tasks(tmp_path)
    incomplete = [t for t in tasks if not t.completed]
    assert len(incomplete) == 2


def test_scan_ignores_non_task_checkboxes(tmp_path):
    note = tmp_path / "note.md"
    note.write_text("- [ ] Not a task\n- [ ] Is a task #task\n")
    tasks = scan_tasks(tmp_path)
    assert len(tasks) == 1
    assert tasks[0].text == "Is a task"


def test_toggle_task_completes(tmp_path):
    note = tmp_path / "note.md"
    note.write_text("- [ ] Do thing #task\n")
    toggle_task(note, line=1)
    content = note.read_text()
    assert "- [x] Do thing #task" in content


def test_toggle_task_uncompletes(tmp_path):
    note = tmp_path / "note.md"
    note.write_text("- [x] Done thing #task\n")
    toggle_task(note, line=1)
    content = note.read_text()
    assert "- [ ] Done thing #task" in content


def test_add_task_to_file(tmp_path):
    note = tmp_path / "inbox.md"
    note.write_text("# Inbox\n")
    add_task(note, "New task")
    content = note.read_text()
    assert "- [ ] New task #task" in content


def test_add_task_creates_file_if_missing(tmp_path):
    note = tmp_path / "2026-05-19.md"
    add_task(note, "First task")
    assert note.exists()
    content = note.read_text()
    assert "- [ ] First task #task" in content


def test_scan_finds_task_tag_at_start(tmp_path):
    note = tmp_path / "note.md"
    note.write_text("- [ ] #task Do something important\n")
    tasks = scan_tasks(tmp_path)
    assert len(tasks) == 1
    assert tasks[0].text == "Do something important"


def test_scan_handles_completed_with_date(tmp_path):
    note = tmp_path / "note.md"
    note.write_text("- [x] #task Set up a sync with team ✅ 2026-03-31\n")
    tasks = scan_tasks(tmp_path)
    assert len(tasks) == 1
    assert tasks[0].completed is True
    assert tasks[0].text == "Set up a sync with team"
