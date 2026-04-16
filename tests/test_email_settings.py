from engine.email_settings import DEFAULT_EMAIL_SETTINGS, load_email_settings, save_email_settings


def test_load_email_settings_returns_defaults_when_missing(tmp_path):
    settings_path = tmp_path / "email_settings.json"

    assert load_email_settings(settings_path) == DEFAULT_EMAIL_SETTINGS


def test_save_and_load_email_settings(tmp_path):
    settings_path = tmp_path / "email_settings.json"

    save_email_settings(
        {
            "host": " smtp.example.com ",
            "port": 465,
            "sender": "school@example.com",
            "username": "mailer",
            "password": "secret",
            "use_tls": False,
            "use_ssl": True,
            "test_email": "admin@example.com",
        },
        settings_path,
    )

    assert load_email_settings(settings_path) == {
        "host": "smtp.example.com",
        "port": "465",
        "sender": "school@example.com",
        "username": "mailer",
        "password": "secret",
        "use_tls": "false",
        "use_ssl": "true",
        "test_email": "admin@example.com",
    }


def test_load_email_settings_ignores_invalid_json(tmp_path):
    settings_path = tmp_path / "email_settings.json"
    settings_path.write_text("{not valid json", encoding="utf-8")

    assert load_email_settings(settings_path) == DEFAULT_EMAIL_SETTINGS
