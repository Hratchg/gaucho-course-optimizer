"""Tests for tests/db_guard.py — the check that keeps pytest off remote databases."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

from tests.db_guard import ALLOW_REMOTE_ENV, database_hosts, remote_database_error

NEON_URL = (
    "postgresql://neondb_owner:s3cret-pw@ep-fake-123-pooler.c-3.us-west-2.aws.neon.tech"
    "/neondb?sslmode=require"
)


class TestDatabaseHosts:
    def test_plain_host(self):
        assert database_hosts("postgresql://gco:gco@localhost:5445/gco_test") == ["localhost"]

    def test_ipv6_brackets_and_case_are_normalised(self):
        assert database_hosts("postgresql://gco:gco@[::1]:5432/db") == ["::1"]
        assert database_hosts("postgresql://gco:gco@LocalHost/db") == ["localhost"]

    def test_query_host_and_hostaddr_count(self):
        url = "postgresql://gco:gco@localhost/db?host=a.example.com&hostaddr=10.0.0.5"
        assert database_hosts(url) == ["localhost", "a.example.com", "10.0.0.5"]

    def test_comma_separated_hosts_are_split(self):
        assert database_hosts("postgresql://gco:gco@localhost,db.example.com/db") == [
            "localhost", "db.example.com",
        ]

    def test_no_host(self):
        assert database_hosts("postgresql:///gco_test") == []


class TestRemoteDatabaseError:
    @pytest.mark.parametrize("url", [
        "postgresql://gco:gco@localhost:5432/gco_test",
        "postgresql://gco:gco@127.0.0.1:5445/gco_test",
        "postgresql://gco:gco@[::1]:5445/gco_test",
        "postgresql+psycopg://gco:gco@LOCALHOST/gco_test",
    ])
    def test_local_hosts_are_allowed(self, url):
        assert remote_database_error(url) is None

    def test_neon_is_refused_and_named_without_the_password(self):
        message = remote_database_error(NEON_URL)
        assert message is not None
        assert "ep-fake-123-pooler.c-3.us-west-2.aws.neon.tech" in message
        assert "s3cret-pw" not in message
        assert ALLOW_REMOTE_ENV in message

    def test_query_host_override_is_refused(self):
        url = "postgresql://gco:gco@localhost/gco_test?host=ep-fake.neon.tech"
        assert "ep-fake.neon.tech" in remote_database_error(url)

    def test_one_remote_host_in_a_list_is_refused(self):
        url = "postgresql://gco:gco@localhost,ep-fake.neon.tech/gco_test"
        assert "ep-fake.neon.tech" in remote_database_error(url)

    def test_missing_host_is_refused(self):
        # libpq would fall back to $PGHOST, which could be anywhere.
        assert "no host" in remote_database_error("postgresql:///gco_test")

    def test_unparseable_url_is_refused_without_echoing_it(self):
        message = remote_database_error("postgres//neondb_owner:s3cret-pw@ep-fake.neon.tech")
        assert message is not None
        assert "s3cret-pw" not in message
        assert "ep-fake" not in message

    def test_override_allows_a_remote_host(self):
        assert remote_database_error(NEON_URL, allow_remote=True) is None


def test_pytest_refuses_to_start_against_a_remote_database():
    """End to end: conftest stops the run before collecting a single test."""
    env = {k: v for k, v in os.environ.items() if k != ALLOW_REMOTE_ENV}
    env["DATABASE_URL"] = NEON_URL
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider"],
        cwd=Path(__file__).resolve().parent.parent,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )
    output = result.stdout + result.stderr
    assert result.returncode == pytest.ExitCode.USAGE_ERROR
    assert "Refusing to run the tests against ep-fake-123-pooler" in output
    assert "s3cret-pw" not in output
    assert "collected" not in output
