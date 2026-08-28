# Farmers Module

The farmer registry is the master list every weight record points to.

## Adding a farmer

Go to **Farmers → Add farmer**. Enter the farmer's name (required, up to 100
characters) and an optional contact number (up to 20 characters). Save, and
the farmer immediately appears in the weight-entry dropdown.

## Editing or removing a farmer

From the Farmers list choose **Edit** next to a farmer to change their name
or contact. Deleting a farmer also removes their weight records and payments
(the database uses ON DELETE CASCADE), so only delete a farmer that was
created by mistake — otherwise keep them for the historical record.

## Farmer data stored

For each farmer the system keeps: an automatic ID, name, contact number and
the date they were registered. Weights, payments and trends are linked to
the farmer by ID, so renaming a farmer never breaks history.
