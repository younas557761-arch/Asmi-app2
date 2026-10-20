# ASMI UI Design System (own CSS, no vendor UI kit)

## Layout shell (every authenticated page)
- Sidebar: #0B1220, fixed 260px, school block top, nav middle,
  ADMINISTRATION section, user card bottom (name + role + logout)
- Auth pages (login/register): NO sidebar, centered card + brand

## Design tokens
| Token | Value |
|---|---|
| --sidebar | #0B1220 |
| --navy | #0F172A |
| --blue | #3B82F6 |
| --cyan | #06B6D4 |
| --bg | #F8FAFC |
| --border | #E2E8F0 |
| Radius | 0.5–0.75rem |

## Components
1. Stat card — label + big number + hint (REAL DB queries only)
2. Module card — checkbox + title + description
3. Stepper — Template → School details → Modules → Review
4. Tabs (pill) — Settings: Profile, Grading, Modules, AI provider, Team, Export
5. Empty state — icon + title + hint
6. Badge — severity/source (info/warning/critical)
7. Quick actions — dashboard shortcuts

## Rules
- No dead buttons: future pages get a "soon" badge, not a 404 link
- No fake numbers
- Light + dark theme (toggle in topbar)
- Mobile: sidebar collapses to top row
