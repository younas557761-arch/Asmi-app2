# ASMI Feature Roadmap

Legend: [DONE] = implemented in Phase 1 | [P2..P5] = upcoming phases

## 1. Authentication
[DONE] Register (email+password), login, logout, password reset (single-use token).
[P2] Email verification (6-digit code, attempt limits, resend) + verification
codes table + pluggable email adapter.
[P5] Optional OAuth (Google) adapter.

## 2. Workspace Setup
[DONE] School tenant + owner membership created in one transaction at registration.
[P4] Onboarding wizard (4 steps): template selection (9 school templates) →
school details → module selection (10 modules) → review → workspace creation
with seeded classes/subjects/fee categories + audit entry.
[P3] Module enable/disable configuration (data never deleted when off).

## 3. Dashboard
[DONE] Shell with stat cards, quick actions, real student count.
[P2] Live summary endpoint: students, attendance-today status, staff count,
fees outstanding + workspace setup checklist.
Real database queries only — no placeholder metrics.

## 4. Core Modules
[DONE] Students: CRUD, search, pagination, duplicate admission-number protection.
[P2] Students CSV import (per-row error report) + export.
[P2] Classes & Subjects: grades, sections, subjects, capacity, promotion.
[P2] Attendance: daily register, 4 statuses, duplicate protection,
correction history, summaries, exports.
[P2] Teachers & Staff: profiles, roles, departments, workload.
[P2] Timetable: weekly grid, rooms, conflict detection, printable.

## 5. Finance & Academics
[P3] Fees: categories, invoices, append-only payment ledger, waivers,
partial payments, balances, receipts.
[P3] Examinations: schedules, marks entry with validation, configurable
grading bands (top-down matching), result publication gate, report cards.
[P3] Reports & analytics: enrollment, attendance trends, fee balances,
exam performance, CSV export.

## 6. People & Communication
[P3] Parents: guardian accounts linked to children.
[P3] Parent Portal: attendance, published results, fee statements,
announcements — strictly scoped to own children.
[P3] Communication: announcements (draft → publish), audience targeting
(everyone / parents / single class), notification preferences,
delivery tracking.

## 7. Settings & Administration [P3]
- School profile (private logo storage)
- Grading scheme editor (bands + pass mark)
- Modules toggle
- Team & access: email invitations → auto membership with role
- Data export (CSV per entity, permission-checked, audit-logged)

## 8. Security & Audit
[DONE] Append-only audit table + writer.
[DONE] Tenant isolation tested (cross-school access denied).
[P3] Audit UI: search, severity filter, source filter.
[P5] Rate limiting, 2FA, session/device management, CSP headers.

## 9. AI Layer [P4]
- Provider-independent AI adapter (credentials server-side)
- Model selection + global AI on/off switch
- Rule-engine fallback: all core operations work with AI disabled
- AI Assistant: chat, suggestion chips, live-figures transparency panel
- School Builder: natural-language commands → typed action plan →
preview → approval gate → apply → audit + report

## 10. Global & Production [P5]
- i18n: English, Urdu, Arabic (RTL), Hindi, French, Spanish, Turkish
- Mobile/low-bandwidth optimization
- Automated backups + tested restore
- Performance and security testing
- Deployment guides (self-host + split hosting)
