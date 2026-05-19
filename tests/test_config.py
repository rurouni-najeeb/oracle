import pytest
from pathlib import Path
from app.config import load_config, AppConfig


def test_load_config_from_file(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text("""
slack:
  channels:
    - general
    - alerts
tasks:
  vault_path: /tmp/vault
  inbox_file: daily
pomodoro:
  work_minutes: 25
  short_break_minutes: 5
  long_break_minutes: 15
  sessions_before_long_break: 4
rss:
  feeds:
    - url: https://example.com/feed.xml
      name: Example
  refresh_interval_minutes: 5
""")
    config = load_config(config_file)
    assert isinstance(config, AppConfig)
    assert config.slack.channels == ["general", "alerts"]
    assert config.tasks.vault_path == Path("/tmp/vault")
    assert config.rss.feeds[0].url == "https://example.com/feed.xml"
    assert config.pomodoro.work_minutes == 25
