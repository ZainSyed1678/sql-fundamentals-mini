-- Everyday staffing reports for the small shop.
-- Run the setup script first: these statements expect the fresh sample data.

-- 1) Hire three new employees, then show every column of every employee.
INSERT INTO employees (id, name, position, salary, department_id) VALUES
    (7, 'Sam',    'Cashier',       2100, 1),
    (8, 'Taylor', 'Support Agent', 2300, 2),
    (9, 'Jamie',  'Stock Helper',  1550, 3);

SELECT * FROM employees ORDER BY id;

-- 2) Inner join: each employee with the name of their department.
SELECT e.name, e.position, d.name AS department
FROM employees e
INNER JOIN departments d ON e.department_id = d.id
ORDER BY e.id;

-- 3) Positions held by more than one employee.
-- WHERE filters rows before grouping; HAVING filters the groups afterwards.
SELECT position, COUNT(*) AS employee_count
FROM employees
GROUP BY position
HAVING COUNT(*) > 1
ORDER BY position;

-- 4) 10% raise for everyone in Sales, then show the Sales rows.
-- ROUND keeps 3000 * 1.1 at 3300.0 instead of 3300.0000000000005.
UPDATE employees
SET salary = ROUND(salary * 1.1, 2)
WHERE department_id IN (SELECT id FROM departments WHERE name = 'Sales');

SELECT e.id, e.name, e.position, e.salary, d.name AS department
FROM employees e
INNER JOIN departments d ON e.department_id = d.id
WHERE d.name = 'Sales'
ORDER BY e.id;

-- 5) Remove everyone in the Temporary department, then prove none remain.
DELETE FROM employees
WHERE department_id IN (SELECT id FROM departments WHERE name = 'Temporary');

SELECT COUNT(*) AS temporary_count
FROM employees e
INNER JOIN departments d ON e.department_id = d.id
WHERE d.name = 'Temporary';

-- 6) Set one employee's salary to an exact value and confirm it.
UPDATE employees SET salary = 2750 WHERE id = 3;

SELECT * FROM employees WHERE id = 3;