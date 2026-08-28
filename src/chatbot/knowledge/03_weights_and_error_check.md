# Weights and the Automatic Error Check

The Weights page is the daily ledger: pick the farmer, the date and the
weighed kilograms, and save. Every entry is checked automatically before it
is stored.

## How the automatic error check works

The check runs on every new weight entry:

1. **Zero or negative weights are rejected** outright with the message
   "reject: must be positive". They are never saved.
2. The system loads the farmer's **last 10 recorded weights**.
3. If the farmer has **fewer than 3 previous records**, the entry is
   accepted as "ok" — there is not enough history to judge.
4. Otherwise the average of that history is computed. If the new weight is
   **more than 3x the average or less than 1/3 of the average**, the entry
   is saved but **flagged** with the warning "warn: please confirm".

## What a flagged entry means

A flagged entry usually means a typo (for example 250 kg instead of 25.0 kg)
or an accidental double entry. Flagged rows are highlighted in the ledger
and are **excluded from payment calculations** until resolved, which
protects both the centre and the farmer from wrong payments.

## Fixing a flagged entry

Check the paper slip or re-weigh, then either correct the weight value
(the corrected entry passes through the check again) or confirm that the
unusual weight is genuine. Payments only count unflagged rows.

## Likely double entries

Entering the same farmer twice on the same date can trigger the range check,
because the second entry compares against a history that already contains
the first. Always check the ledger for the date before adding a new row.
