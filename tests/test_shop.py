import os
import sqlite3
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import run_sql  # noqa: E402


def read_sql(name):
    with open(os.path.join(ROOT, name), encoding="utf-8-sig") as handle:
        return handle.read()


def fresh_db():
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = ON")
    run_sql.run_script(conn, read_sql("shop_setup.sql"))
    return conn


class SetupTests(unittest.TestCase):
    def setUp(self):
        self.conn = fresh_db()

    def tearDown(self):
        self.conn.close()

    def test_tables_have_the_required_columns(self):
        emp_cols = [r[1] for r in self.conn.execute("PRAGMA table_info(employees)")]
        dept_cols = [r[1] for r in self.conn.execute("PRAGMA table_info(departments)")]
        self.assertEqual(emp_cols, ["id", "name", "position", "salary", "department_id"])
        self.assertEqual(dept_cols, ["id", "name", "location"])

    def test_seed_has_three_departments_and_six_employees(self):
        names = [r[0] for r in self.conn.execute("SELECT name FROM departments ORDER BY id")]
        self.assertEqual(names, ["Sales", "Support", "Temporary"])
        count = self.conn.execute("SELECT COUNT(*) FROM employees").fetchone()[0]
        self.assertEqual(count, 6)

    def test_every_department_has_employees(self):
        rows = self.conn.execute(
            "SELECT department_id, COUNT(*) FROM employees GROUP BY department_id").fetchall()
        self.assertEqual(dict(rows), {1: 2, 2: 2, 3: 2})

    def test_setup_can_be_run_twice(self):
        run_sql.run_script(self.conn, read_sql("shop_setup.sql"))
        count = self.conn.execute("SELECT COUNT(*) FROM employees").fetchone()[0]
        self.assertEqual(count, 6)

    def test_unknown_department_is_rejected(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute(
                "INSERT INTO employees VALUES (50, 'Ghost', 'Cashier', 1000, 99)")


class ReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.conn = fresh_db()
        cls.results = run_sql.run_script(cls.conn, read_sql("reports.sql"))

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()

    def test_six_reports_are_produced(self):
        self.assertEqual(len(self.results), 6)

    def test_1_three_new_employees_are_listed(self):
        columns, rows = self.results[0]
        self.assertEqual(columns, ["id", "name", "position", "salary", "department_id"])
        self.assertEqual(len(rows), 9)
        self.assertEqual([r[1] for r in rows[6:]], ["Sam", "Taylor", "Jamie"])

    def test_2_join_lists_name_position_department(self):
        columns, rows = self.results[1]
        self.assertEqual(columns, ["name", "position", "department"])
        self.assertEqual(len(rows), 9)
        self.assertIn(("Pat", "Cashier", "Sales"), rows)
        self.assertIn(("Jamie", "Stock Helper", "Temporary"), rows)

    def test_3_only_positions_with_more_than_one_employee(self):
        columns, rows = self.results[2]
        self.assertEqual(columns, ["position", "employee_count"])
        self.assertEqual(rows, [("Cashier", 2), ("Stock Helper", 3), ("Support Agent", 3)])
        self.assertNotIn("Sales Lead", [r[0] for r in rows])

    def test_4_sales_get_exactly_ten_percent(self):
        _, rows = self.results[3]
        salaries = {r[1]: r[3] for r in rows}
        self.assertEqual(salaries, {"Pat": 2200, "Morgan": 3300, "Sam": 2310})
        self.assertTrue(all(r[4] == "Sales" for r in rows))

    def test_4_other_departments_keep_their_salary(self):
        salary = self.conn.execute("SELECT salary FROM employees WHERE id = 4").fetchone()[0]
        self.assertEqual(salary, 2500)

    def test_5_no_temporary_employees_remain(self):
        columns, rows = self.results[4]
        self.assertEqual(columns, ["temporary_count"])
        self.assertEqual(rows, [(0,)])
        left = self.conn.execute("SELECT COUNT(*) FROM employees").fetchone()[0]
        self.assertEqual(left, 6)

    def test_6_single_salary_update_is_confirmed(self):
        _, rows = self.results[5]
        self.assertEqual(rows, [(3, "Alex", "Support Agent", 2750.0, 2)])


class RunnerTests(unittest.TestCase):
    def test_split_ignores_semicolons_in_comments_and_text(self):
        sql = "-- note; not the end\r\nSELECT 'a;b';\r\nSELECT 2;\r\n"
        self.assertEqual(run_sql.split_statements(sql),
                         ["-- note; not the end\nSELECT 'a;b';", "SELECT 2;"])

    def test_missing_semicolon_is_reported(self):
        with self.assertRaises(ValueError):
            run_sql.split_statements("SELECT 1")

    def test_trailing_comment_is_fine(self):
        self.assertEqual(run_sql.split_statements("SELECT 1;\n-- done\n"), ["SELECT 1;"])

    def test_main_writes_a_database_file(self):
        with tempfile.TemporaryDirectory() as folder:
            db_path = os.path.join(folder, "scratch.db")
            out = StringIO()
            with redirect_stdout(out):
                code = run_sql.main([db_path, os.path.join(ROOT, "shop_setup.sql"),
                                     os.path.join(ROOT, "reports.sql")])
            self.assertEqual(code, 0)
            self.assertIn("temporary_count\n0\n(1 row)", out.getvalue())
            conn = sqlite3.connect(db_path)
            try:
                count = conn.execute("SELECT COUNT(*) FROM employees").fetchone()[0]
            finally:
                conn.close()
            self.assertEqual(count, 6)

    def test_running_reports_twice_fails_cleanly(self):
        conn = fresh_db()
        run_sql.run_script(conn, read_sql("reports.sql"))
        with self.assertRaises(sqlite3.IntegrityError):
            run_sql.run_script(conn, read_sql("reports.sql"))
        conn.close()


if __name__ == "__main__":
    unittest.main()