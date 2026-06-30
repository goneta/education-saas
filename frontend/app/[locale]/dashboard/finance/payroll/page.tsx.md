# page.tsx (Finance › Payroll)
## Source File
- `frontend/app/[locale]/dashboard/finance/payroll/page.tsx`
## Purpose
- Admin/accountant Payroll UI (#7). Two tabs: Salary profiles (per-employee config — employee type, pay type, base rate, currency, contribution/tax %) and Payslips (TableFilter list, generate modal with itemised lines, approve, pay with method+reference, print-friendly payslip detail). Exports `PayslipModal` reused by self-service. Talks to `/finance/payroll/*`. i18n `payroll` namespace.
## Maintenance Notes
- Rates shown as % but sent as fractions (÷100). Employee picker merges `/personnel` + `/teachers`. Payment methods: bank_transfer/cash/stripe/cinetpay/djamo.
