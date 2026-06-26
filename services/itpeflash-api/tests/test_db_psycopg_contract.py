from __future__ import annotations

from unittest.mock import MagicMock, patch
from uuid import UUID

import psycopg

from app.db import SnapshotRepository
from app.models import AuthenticatedUser, Note, Snapshot
from scripts.migrate import seed_cards


# ---------------------------------------------------------------------------
# psycopg3 API contract
# ---------------------------------------------------------------------------


def test_psycopg_connection_has_no_executemany() -> None:
    """psycopg3 puts executemany on Cursor only; Connection has none.

    If this test breaks, psycopg grew a Connection.executemany — review db.py
    and migrate.py to see if the cursor-based calls can be simplified.
    """
    assert not hasattr(psycopg.Connection, "executemany"), (
        "psycopg.Connection now has executemany — recheck db.py and migrate.py"
    )


def test_psycopg_cursor_has_executemany() -> None:
    assert hasattr(psycopg.Cursor, "executemany")


# ---------------------------------------------------------------------------
# Mock helpers
# ---------------------------------------------------------------------------


def _cursor_mock() -> MagicMock:
    cur = MagicMock()
    cur.__enter__.return_value = cur
    cur.__exit__.return_value = False
    return cur


def _conn_mock(cur: MagicMock) -> MagicMock:
    """Connection mock spec'd to psycopg.Connection.

    Accessing .executemany raises AttributeError (same as the real object),
    so any code that calls connection.executemany() will fail this test.
    """
    conn = MagicMock(spec=psycopg.Connection)
    conn.__enter__.return_value = conn
    conn.__exit__.return_value = False

    result = MagicMock()
    result.fetchall.return_value = []
    result.fetchone.return_value = {"updated_at": None}
    conn.execute.return_value = result
    conn.cursor.return_value = cur

    txn = MagicMock()
    txn.__enter__.return_value = txn
    txn.__exit__.return_value = False
    conn.transaction.return_value = txn

    return conn


# ---------------------------------------------------------------------------
# migrate.seed_cards
# ---------------------------------------------------------------------------


def test_seed_cards_uses_cursor_executemany() -> None:
    """seed_cards() must route executemany through cursor(), not connection."""
    cur = _cursor_mock()
    conn = _conn_mock(cur)

    # cards=[] → rows=[] but executemany is still called unconditionally
    seed_cards(conn, [], UUID("00000000-0000-0000-0000-000000000001"), "t@test.com")

    cur.executemany.assert_called_once()


# ---------------------------------------------------------------------------
# SnapshotRepository.save
# ---------------------------------------------------------------------------


def _note(note_id: str = "n1") -> Note:
    return Note(
        id=note_id,
        title="T",
        domain="D",
        tags=[],
        importance=1,
        source="s",
        created="2026-01-01",
        summary="s",
        problem="p",
        content="<p></p>",
        mnemonics=[],
        memo="",
        deleted=False,
    )


def test_save_uses_cursor_executemany_for_note_rows() -> None:
    """save() must call cursor.executemany() for note_rows."""
    cur = _cursor_mock()
    conn = _conn_mock(cur)

    user = AuthenticatedUser(id="00000000-0000-0000-0000-000000000001", email="t@test.com")
    snapshot = Snapshot(notes=[_note()], statuses={})
    dummy = Snapshot(notes=[_note()], statuses={})

    repo = SnapshotRepository("postgresql://fake/db")
    with patch.object(repo, "_connect", return_value=conn), \
         patch.object(repo, "load", return_value=dummy):
        repo.save(user, snapshot)

    cur.executemany.assert_called_once()


def test_save_uses_cursor_executemany_for_both_rows() -> None:
    """save() must call cursor.executemany() twice when both note_rows and status_rows exist."""
    cur = _cursor_mock()
    conn = _conn_mock(cur)

    user = AuthenticatedUser(id="00000000-0000-0000-0000-000000000001", email="t@test.com")
    snapshot = Snapshot(notes=[_note()], statuses={"n1": "review"})
    dummy = Snapshot(notes=[_note()], statuses={"n1": "review"})

    repo = SnapshotRepository("postgresql://fake/db")
    with patch.object(repo, "_connect", return_value=conn), \
         patch.object(repo, "load", return_value=dummy):
        repo.save(user, snapshot)

    assert cur.executemany.call_count == 2
