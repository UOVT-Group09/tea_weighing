# Reports and the Trend Estimate

The Reports section turns the ledger into daily and per-farmer summaries,
with optional charts.

## Daily report

Shows every weight entry for a chosen date, the day's total kilograms, how
many farmers delivered, and how many entries were flagged. Use it at the
end of each day to reconcile against the paper slips.

## Farmer report

Shows one farmer's full history: every weight entry, totals, flagged rows
and the trend card.

## How the trend estimate works

The trend is a simple **moving average** — deliberately rule-based, not
machine learning:

1. Take the farmer's **last 7 recorded weights**.
2. If there are fewer than 3 records, no trend is shown (not enough data).
3. Compute the average of those weights — this is also the rough estimate
   for the next delivery.
4. If the latest weight is above the average the trend is **up**;
   otherwise **down**.

## Using the trend

The trend helps the operator plan: an "up" trend for many farmers means
more leaf is coming and transport/cash should be arranged; a sudden "down"
trend for one farmer may be worth a phone call. It is an estimate, not a
guarantee.
