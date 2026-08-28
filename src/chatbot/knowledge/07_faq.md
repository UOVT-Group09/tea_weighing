# Frequently Asked Questions

## Why was a weight entry flagged?

The automatic check compares each new weight with the farmer's average of
their last 10 entries. Anything more than 3x the average or below 1/3 of
it is saved but flagged for confirmation. Zero or negative weights are
rejected entirely. See the Weights section of the manual for details.

## Why is the dashboard showing "Database offline"?

MySQL is unreachable. Check that the MySQL service is running and that the
DB_HOST, DB_PORT, DB_NAME, DB_USER and DB_PASSWORD values in the `.env`
file are correct, then refresh the page.

## How do I change the tea price per kg?

Add a new row to the price configuration with today's effective date. The
system always uses the price with the latest effective date; older prices
stay stored for auditing. If no price is set, LKR 250/kg is used.

## Can the chatbot change or delete data?

No. The assistant is read-only by design — it can look up farmers,
weights, payments, attendance and prices, but every change must be made by
the operator through the normal pages. This is a deliberate safety rule.

## I forgot the operator password

The default account is created from DEFAULT_OPERATOR_USERNAME and
DEFAULT_OPERATOR_PASSWORD in the `.env` file on first run. An
administrator can reset the password directly in the operator table, or
re-seed by clearing the table and restarting with the desired values in
`.env`.

## Does the system work offline?

The web app runs on the local network without internet; only the AI
chatbot needs internet to reach the free Groq API. Without an API key the
chatbot still answers from this built-in manual ("manual mode").
