import importlib


def load_config(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    import void.config as config

    return importlib.reload(config)


def test_config_setup_creates_dirs(tmp_path, monkeypatch):
    config = load_config(tmp_path, monkeypatch)

    assert config.Config.BASE_DIR == tmp_path / ".void"
    assert config.Config.DB_PATH == config.Config.BASE_DIR / "void.db"

    expected_dirs = [
        config.Config.BASE_DIR,
        config.Config.LOG_DIR,
        config.Config.BACKUP_DIR,
        config.Config.EXPORTS_DIR,
        config.Config.CACHE_DIR,
        config.Config.REPORTS_DIR,
        config.Config.MONITOR_DIR,
        config.Config.SCRIPTS_DIR,
    ]

    for directory in expected_dirs:
        assert directory.exists()
