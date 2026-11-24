# rote report — intake.mp4

- **2 attempt(s)**, last replay **passed**
- **$0.00390** over 2 model calls (4,974 in / 7,475 out, 70% cached)
- wall time 19s
- proof data: fresh — never in the recording

## What it understood

**Goal.** Record received parts on the Parts intake page by adding one intake line per part and submitting the intake.

**Success looks like.** The intake is submitted and a green confirmation toast appears at the bottom right reading 'Intake submitted — 2 lines recorded.' The entered lines remain listed in the table below the form.

| step | action | target | value | scope |
|---|---|---|---|---|
| 1 | type | SKU | `{sku}` | each_row |
| 2 | type | Description | `{description}` | each_row |
| 3 | type | Quantity | `{quantity}` | each_row |
| 4 | type | Unit cost | `{unit_cost}` | each_row |
| 5 | select | Supplier | `{supplier}` | each_row |
| 6 | select | Location | `{location}` | each_row |
| 7 | click | Add line | `` | each_row |
| 8 | submit | Submit intake | `` | once |

**Controls found:**
`SKU` (text), `Description` (text), `Quantity` (number), `Unit cost` (number), `Supplier` (select), `Location` (select)

**Example rows from the recording:**

```json
[
 {
  "sku": "BRK-2041",
  "description": "Brake pad set, front",
  "quantity": "12",
  "unit_cost": "18.40",
  "supplier": "Northwind Supply",
  "location": "Aisle 4 · Bay 2"
 },
 {
  "sku": "FLT-1180",
  "description": "Oil filter, spin-on",
  "quantity": "40",
  "unit_cost": "6.25",
  "supplier": "Bergen Parts",
  "location": "Aisle 7 · Bay 1"
 }
]
```

## Proof

| check | result | detail |
|---|---|---|
| script runs on fresh data | ✅ | 2 row(s) through intake.py |
| the loop completed one cycle per row | ✅ | 2 iterations, each ending on app.html |
| every value was accepted by its control | ✅ | all 12 values were typed and confirmed on screen |
| the values are visible on the final page | ✅ | all 12 values found |
| the app reached the state the recording ended in | ✅ | matched the expected end state |
| the app stored exactly the rows we sent | ✅ | 2/2 rows stored as sent |
| the task was submitted | ✅ | 2 record(s) confirmed by the app |
| the repeating block commits each row | ✅ | 1 committing step(s) inside steps 1–7 |

After the replay: `proof_attempt2.png`

## Attempts

### Attempt 1 — failed
- ❌ the app stored exactly the rows we sent: sent 2 row(s), the app holds 1
- ❌ the repeating block commits each row: steps 1–2 only enter data, with no click or submit, so 2 rows would overwrite the same form and produce one result instead of 2

### Attempt 2 — passed

## Cost

| what | calls | tokens in | cached | tokens out | $ |
|---|---|---|---|---|---|
| intake | 1 | 2,812 | 2,748 | 2,543 | 0.00129 |
| repair | 1 | 2,162 | 756 | 4,932 | 0.00261 |

Raw per-call trace: `results/demo/intake/ledger.jsonl`

