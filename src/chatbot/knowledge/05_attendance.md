# Attendance Module

Attendance records which pluckers worked on which days, and it directly
drives the wage calculation.

## Registering a plucker

Go to **Attendance → Add plucker**. Enter the plucker's name and their
daily rate in LKR. The daily rate can differ per plucker.

## Marking attendance

On the Attendance page pick the date and tick the pluckers who were
present, then save. Each plucker can only have one attendance record per
day (the database enforces this), so re-saving a day updates it rather
than duplicating it.

## Attendance and wages

The Payments page counts each plucker's days marked present and multiplies
by their daily rate. Days that were never marked count as absent, so mark
attendance every working day or wages will be understated.
