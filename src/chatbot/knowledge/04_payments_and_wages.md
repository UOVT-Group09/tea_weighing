# Payments and Wages

The Payments page shows what each farmer should be paid and what each
plucker has earned. All amounts are in Sri Lankan Rupees (LKR).

## Farmer payment formula

    payment = total unflagged kilograms x current price per kg

Only **unflagged** weight records count — entries flagged by the error
check are excluded until they are corrected or confirmed. This is why a
farmer's payment can look lower than their delivered total.

## Tea price per kg

The price comes from the price configuration table: the row with the most
recent effective date is the active price. If no price has been configured
yet, the system falls back to a default of **LKR 250 per kg**. To change
the price, insert a new price row with a new effective date — old prices
are kept for the record.

## Plucker wage formula

    wage = days marked present x the plucker's daily rate

Each plucker has their own daily rate, set when the plucker is registered.
Attendance is marked on the Attendance page; only days marked "present"
count toward the wage.

## Why is a farmer's payment lower than expected?

The usual causes: some of their entries were flagged by the error check
(flagged rows are excluded), the price per kg changed, or a weight was
recorded under the wrong farmer. Check the farmer's report page and the
flagged records list first.
