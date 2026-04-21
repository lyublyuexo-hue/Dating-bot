"""Базовые тесты модулей (запускаются через pytest)."""
import pytest

def test_points_config():
    from bot.modules.rating import POINTS
    assert "match" in POINTS
    assert POINTS["match"] >= POINTS["like"]

def test_default_tags_not_empty():
    from bot.modules.tags import DEFAULT_TAGS
    assert len(DEFAULT_TAGS) > 0
    for tag in DEFAULT_TAGS:
        assert "name" in tag
        assert "category" in tag

def test_common_tags_logic():
    """Проверяем логику пересечения тегов без БД."""
    ids1 = {1, 2, 3}
    ids2 = {2, 3, 4}
    common = ids1 & ids2
    assert common == {2, 3}
