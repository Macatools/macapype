"""Test should only pass in CircleCI environment"""
import os
import ci_info

def test_circle(tmpdir):
    IS_REAL_PR = bool(
        os.getenv("CIRCLE_PULL_REQUEST") and
        os.getenv("CIRCLE_PULL_REQUEST") != "false"
    )
    assert ci_info.name() == "CircleCI"
    assert ci_info.is_ci() is True
    assert ci_info.is_pr() == IS_REAL_PR

    assert ci_info.info() == {
        "name": "CircleCI",
        "is_ci": True,
        "is_pr": IS_REAL_PR
    }
