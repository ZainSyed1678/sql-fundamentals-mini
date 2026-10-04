"""Run .sql files against a SQLite database file and print every query result.

DBeaver is where you write and explore the SQL; this script replays the very
same files from the terminal so the results can be checked and tested.
"""
import os
import sqlite3
import sys


def split_statements(sql_text):
    """Cut a script into complete statements, one per list item."""
    statements = []
    current = ""
    for line in sql_text.splitlines():
        current += line + "\n"
        # complete_statement knows about quotes and -- comments, so a ';'
        # inside 'text' or a comment does not end the statement early.
        if sqlite3.complete_statement(current):
            statements.append(current.strip())
            current = ""
    if current.strip() and not _only_comments(current):
        raise ValueError("Unfinished statement (missing ';'?):\n" + current.strip())
    return statements


def _only_comments(text):
    return all(not line.strip() or line.strip().startswith("--")
               for line in text.splitlines())


def run_script(conn, sql_text):
    """Execute each statement; return (columns, rows) for every query that returns rows."""
    results = []
    for statement in split_statements(sql_text):
        cursor = conn.execute(statement)
        if cursor.description is not None:
            columns = [col[0] for col in cursor.description]
            results.append((columns, cursor.fetchall()))
    conn.commit()
    return results


def format_result(columns, rows):
    lines = [" | ".join(columns)]
    for row in rows:
        lines.append(" | ".join(str(value) for value in row))
    lines.append("(%d row%s)" % (len(rows), "" if len(rows) == 1 else "s"))
    return "\n".join(lines)


def main(args):
    if len(args) < 2:
        script_name = os.path.basename(__file__)
        print("Usage: python " + script_name + " DATABASE_FILE SCRIPT.sql [MORE.sql ...]")
        return 1
    db_path = os.path.abspath(args[0])
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        for script in args[1:]:
            # utf-8-sig also accepts files that Windows saved with a BOM.
            with open(os.path.abspath(script), encoding="utf-8-sig") as handle:
                sql_text = handle.read()
            print("== " + os.path.basename(script) + " ==")
            results = run_script(conn, sql_text)
            for columns, rows in results:
                print(format_result(columns, rows))
                print()
            if not results:
                print("OK (no query results)")
                print()
    except (sqlite3.Error, ValueError) as error:
        print("ERROR: %s" % error)
        return 1
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))