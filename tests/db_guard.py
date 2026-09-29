"""Keep the test suite off real databases.

The session fixture in conftest.py ends with ``Base.metadata.drop_all()``, and
test_migrations.py creates and drops scratch databases on the same server, so
running pytest with production's DATABASE_URL would drop production's tables.
"""

from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError

LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}
ALLOW_REMOTE_ENV = "ALLOW_REMOTE_TEST_DB"


def database_hosts(url: str) -> list[str]:
    """Every host a connection to url could reach, lowercased.

    libpq accepts comma-separated host lists, and ``?host=`` or ``?hostaddr=``
    in the query string take precedence over the URL's own host, so all of
    them count. A URL with no host at all returns [].
    """
    parsed = make_url(url)
    hosts = [parsed.host] if parsed.host else []
    for key in ("host", "hostaddr"):
        value = parsed.query.get(key, ())
        hosts.extend([value] if isinstance(value, str) else value)
    return [h.strip().strip("[]").lower() for item in hosts for h in item.split(",")]


def remote_database_error(url: str, allow_remote: bool = False) -> str | None:
    """Why the tests must not run against url, or None when it is safe.

    Only localhost, 127.0.0.1 and ::1 are safe unless allow_remote is set. A
    URL with no host is refused too: libpq would fall back to $PGHOST. The
    message names the host but never the password.
    """
    if allow_remote:
        return None

    advice = (
        "Point DATABASE_URL at a throwaway local database (localhost, 127.0.0.1 "
        "or ::1), or set "
        f"{ALLOW_REMOTE_ENV}=1 if you really mean to use this one."
    )
    try:
        hosts = database_hosts(url)
    except ArgumentError:
        return f"Refusing to run the tests: DATABASE_URL is not a valid database URL. {advice}"

    if not hosts:
        return (
            "Refusing to run the tests: DATABASE_URL has no host, so libpq "
            f"would use $PGHOST or a Unix socket. {advice}"
        )
    remote = [h for h in hosts if h not in LOCAL_HOSTS]
    if not remote:
        return None
    return (
        f"Refusing to run the tests against {', '.join(remote)}: the test "
        f"session drops every table when it ends. {advice}"
    )
