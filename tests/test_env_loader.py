from call_summariser import env_loader


def test_env_loader_does_not_override_existing_environment(monkeypatch):
    calls = []
    monkeypatch.setattr(env_loader, "load_dotenv", lambda **kwargs: calls.append(kwargs))
    env_loader.load_dotenv_if_available()
    assert calls == [{"override": False}]
