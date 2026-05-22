from __future__ import annotations

import pytest

from slices.health_check.schemas import HttpStatus
from slices.health_check.service import classify_http_status


@pytest.mark.parametrize(
    "code,expected",
    [
        (200, HttpStatus.ok),
        (201, HttpStatus.ok),
        (301, HttpStatus.redirect),
        (302, HttpStatus.redirect),
        (400, HttpStatus.client_error),
        (404, HttpStatus.client_error),
        (500, HttpStatus.server_error),
        (503, HttpStatus.server_error),
    ],
)
def test_classify_http_status(code: int, expected: HttpStatus) -> None:
    assert classify_http_status(code) == expected
