from news_analyst.config import load_config


def test_load_config() -> None:
    config = load_config("config.yaml")
    assert config.report.title
    assert "mexico" in config.segments
    assert config.segments["mexico"].sources
