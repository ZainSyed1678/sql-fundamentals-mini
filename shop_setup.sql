-- Small shop database: build both tables from scratch and fill them with sample data.
-- Safe to run again at any time: it drops the old tables first.

-- employees points at departments, so it must be dropped first.
DROP TABLE IF EXISTS employees;
DROP TABLE IF EXISTS departments;

CREATE TABLE departments (
    id       INTEGER PRIMARY KEY,
    name     TEXT NOT NULL,
    location TEXT NOT NULL
);

CREATE TABLE employees (
    id            INTEGER PRIMARY KEY,
    name          TEXT NOT NULL,
    position      TEXT NOT NULL,
    salary        REAL NOT NULL,
    department_id INTEGER REFERENCES departments(id)
);

INSERT INTO departments (id, name, location) VALUES
    (1, 'Sales',     'Front Counter'),
    (2, 'Support',   'Back Office'),
    (3, 'Temporary', 'Stockroom');

INSERT INTO employees (id, name, position, salary, department_id) VALUES
    (1, 'Pat',    'Cashier',        2000, 1),
    (2, 'Morgan', 'Sales Lead',     3000, 1),
    (3, 'Alex',   'Support Agent',  2400, 2),
    (4, 'Jordan', 'Support Agent',  2500, 2),
    (5, 'Casey',  'Stock Helper',   1500, 3),
    (6, 'Riley',  'Stock Helper',   1600, 3);