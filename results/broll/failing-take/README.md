# The failing take

A real run of `rote learn` on the intake task with two rows, kept because it shows the
behaviour the video has to show honestly: the first plan was wrong, the verdict caught it,
and the repair fixed it.

| attempt | verdict | the check that failed |
|---|---|---|
| 1 | **failed** | the app stored exactly the rows we sent: sent 2 row(s), the app holds 1; the repeating block commits each row: steps 1–2 only enter data, with no click or submit, so 2 rows would overwrite the same form and produce one result instead of 2 |
| 2 | passed | — |

Total cost of this take: $0.00550 over 2 model calls.

What the failure looked like: `proof_attempt1.png` — the table holds one line and the toast
says "1 line recorded", because the repeating block typed both rows into the same form and
only the second survived.

What the repair changed: the repeating range moved from steps 1–2 to 1–7, which pulls the
click that commits a line inside the loop. `proof_attempt2.png` shows both lines landing.
