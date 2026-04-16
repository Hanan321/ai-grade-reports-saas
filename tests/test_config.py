from config.default_config import load_app_config


def test_load_app_config_defaults_to_saas(monkeypatch):
    monkeypatch.delenv("APP_MODE", raising=False)

    app_config = load_app_config()

    assert app_config.mode == "saas"
    assert app_config.branding.app_name == "Student Grade Report Cleaner"
    assert app_config.branding.show_branding is False
    assert app_config.grade_report.high_performer_score_threshold == 85.0


def test_load_app_config_can_select_school_mode(monkeypatch):
    monkeypatch.setenv("APP_MODE", "school")

    app_config = load_app_config()

    assert app_config.mode == "school"
    assert app_config.branding.show_branding is True
    assert app_config.branding.school_name == "Demo Private School"
    assert app_config.grade_report.weights["exam_score"] == 0.50
    assert app_config.grade_report.high_performer_score_threshold == 90.0


def test_invalid_app_mode_falls_back_to_saas(monkeypatch):
    monkeypatch.setenv("APP_MODE", "unknown")

    app_config = load_app_config()

    assert app_config.mode == "saas"
