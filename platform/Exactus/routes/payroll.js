// routes/payroll.js
const express = require('express');
const router = express.Router();
const rbac = require('../middleware/rbacMiddleware');

// Payroll routes with RBAC protection
router.post(
    '/payruns',
    rbac.requirePermission('PAYRUN', 'CREATE'),
    payrollController.createPayrun
);

router.get(
    '/payruns',
    rbac.requirePermission('PAYRUN', 'READ'),
    payrollController.getPayruns
);

router.put(
    '/payruns/:id',
    rbac.requirePermission('PAYRUN', 'UPDATE'),
    payrollController.updatePayrun
);

router.delete(
    '/payruns/:id',
    rbac.requirePermission('PAYRUN', 'DELETE'),
    payrollController.deletePayrun
);

// Employee management
router.get(
    '/employees',
    rbac.requirePermission('EMPLOYEE', 'READ'),
    employeeController.getEmployees
);

router.post(
    '/employees',
    rbac.requirePermission('EMPLOYEE', 'CREATE'),
    employeeController.createEmployee
);

// Financial reporting (FINANCE role only)
router.get(
    '/reports/payroll',
    rbac.requirePermission('PAYREGISTER', 'READ'),
    reportsController.getPayrollReport
);

module.exports = router;