from __future__ import annotations
import re

_question_mark_outside_quotes = re.compile(r"""
    (')                                     # group 1: opening single quote
    (?:\\.|[^\\'])*                         #   any escaped char or non-quote
    (')                                     # group 2: closing single quote
    |                                       # OR
    (\?)                                    # group 3: a literal question mark
""", re.VERBOSE)

def to_psql(sql: str) -> str:
    """Convert SQLite-style '?' placeholders to Postgres '%s' safely (not inside quoted strings)."""
    out = []
    i = 0
    in_string = False
    while i < len(sql):
        ch = sql[i]
        if ch == "'" and (i == 0 or sql[i-1] != "\\"):
            in_string = not in_string
            out.append(ch)
            i += 1
            continue
        if ch == "?" and not in_string:
            out.append("%s")
        else:
            out.append(ch)
        i += 1
    return "".join(out)

def execute(cur, sql: str, params=None):
    """Drop-in replacement for cursor.execute(sql, params) that tolerates '?' binds on Postgres."""
    cur.execute(to_psql(sql), params or [])
