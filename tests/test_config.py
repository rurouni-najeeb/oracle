from pathlib import Path
from app.config import AppConfig, build_github_repository, load_config, save_config


def test_load_config_from_file(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text("""
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
github:
  orgs:
    - moia-dev
  repositories:
    - owner: moia-dev
      repo: oracle
      display_name: Oracle
      url: https://github.com/moia-dev/oracle
""")
    config = load_config(config_file)
    assert isinstance(config, AppConfig)
    assert config.tasks.vault_path == Path("/tmp/vault")
    assert config.rss.feeds[0].url == "https://example.com/feed.xml"
    assert config.pomodoro.work_minutes == 25
    assert config.github.orgs == ["moia-dev"]
    assert config.github.repositories[0].full_name == "moia-dev/oracle"
    assert config.github.repositories[0].label == "Oracle"


def test_build_github_repository_from_owner_repo():
    repo = build_github_repository("moia-dev/oracle", "Oracle")
    assert repo.owner == "moia-dev"
    assert repo.repo == "oracle"
    assert repo.url == "https://github.com/moia-dev/oracle"
    assert repo.label == "Oracle"


def test_build_github_repository_from_bare_www_url():
    repo = build_github_repository("www.github.com/moia-dev/oracle/pulls")
    assert repo.full_name == "moia-dev/oracle"
    assert repo.url == "https://github.com/moia-dev/oracle"


def test_load_repository_name_as_display_label(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text("""
github:
  repositories:
    - name: Oracle
      url: https://github.com/moia-dev/oracle
""")
    config = load_config(config_file)
    assert config.github.repositories[0].label == "Oracle"
    assert config.github.repositories[0].full_name == "moia-dev/oracle"


def test_save_config_includes_github_repositories(tmp_path):
    config_file = tmp_path / "config.yaml"
    config = AppConfig()
    config.github.repositories.append(build_github_repository("moia-dev/oracle"))

    save_config(config, config_file)

    reloaded = load_config(config_file)
    assert reloaded.github.repositories[0].full_name == "moia-dev/oracle"
