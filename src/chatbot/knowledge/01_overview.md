# System Overview

The Tea Leaves Weighing & Smart Records System is a Flask + MySQL web
application for small tea collection centres in Sri Lanka. It digitises the
daily collection ledger and automatically catches entry errors, replacing
paper books that cause payment disputes.

## Who uses the system

A collection centre **operator** logs in with a username and password and
records everything on behalf of farmers and pluckers. Farmers deliver green
tea leaf to the centre; pluckers are day-labourers paid a daily rate. The
default operator account is created automatically on first run (username
`admin` unless changed in the `.env` configuration).

## Main modules

- **Farmers** — register and manage the farmers who deliver leaf.
- **Weights** — record each day's weighed amounts; every entry passes the
  automatic error check.
- **Payments** — farmer payments (kg x price) and plucker wages
  (days present x daily rate).
- **Attendance** — mark which pluckers worked each day.
- **Reports** — daily and per-farmer reports, plus the supply trend estimate.

## Logging in and out

Open the site and you land on the login page. Enter the operator username
and password, then press Log in. Use the "Log out" button in the top-right
of the navigation bar to end the session. All pages except login require an
active session.

## Database offline badge

The app starts even when MySQL is unreachable — the dashboard shows a
"Database offline" badge. Fix the connection settings in `.env`
(DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD) and make sure the MySQL
service is running, then refresh.
