from __future__ import annotations

from types import SimpleNamespace

import pytest

from ldsrs2_launcher.config.schema import StagingConfig
from ldsrs2_launcher.data import staging


class RateLimitError(Exception):
    def __init__(self, message: str = "429 Too Many Requests") -> None:
        super().__init__(message)
        self.response = SimpleNamespace(status_code=429)


def test_create_cube_with_retry_succeeds_after_retries(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = {"count": 0}

    def fake_create(**_: object) -> str:
        calls["count"] += 1
        if calls["count"] < 3:
            raise RateLimitError()
        return "cube"

    sleeps: list[int] = []
    monkeypatch.setattr(staging.cubo, "create", fake_create)
    monkeypatch.setattr(staging.time, "sleep", lambda delay: sleeps.append(delay))

    config = StagingConfig(rate_limit_retry_delays_seconds=[15, 30, 60])
    result = staging.create_cube_with_retry(
        latitude=1.0,
        longitude=2.0,
        start_date="2025-01-01",
        end_date="2025-01-02",
        config=config,
    )

    assert result == "cube"
    assert sleeps == [15, 30]


def test_create_cube_with_retry_raises_after_schedule_exhausted(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(staging.cubo, "create", lambda **_: (_ for _ in ()).throw(RateLimitError()))
    monkeypatch.setattr(staging.time, "sleep", lambda _: None)

    config = StagingConfig(rate_limit_retry_delays_seconds=[15, 30])
    with pytest.raises(RuntimeError, match="retry policy was exhausted"):
        staging.create_cube_with_retry(
            latitude=1.0,
            longitude=2.0,
            start_date="2025-01-01",
            end_date="2025-01-02",
            config=config,
        )
