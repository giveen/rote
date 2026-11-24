# rote report — intake.mp4

- **2 attempt(s)**, last replay **passed**
- **$0.00353** over 2 model calls (4,934 in / 6,278 out, 22% cached)
- wall time 18s
- proof data: fresh — never in the recording

## What it understood

**Goal.** Log goods received against a purchase order on the Parts intake page by adding each part as a line and submitting the intake.

**Success looks like.** The entered lines appear in the table below the form with SKU, Description, Qty, Unit Cost, Supplier, and Location, the intake form is cleared to its placeholders, and a green confirmation at the bottom right states 'Intake submitted — 2 lines recorded.'

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
| every value was accepted by its control | ✅ | all 12 values were typed and confirmed on screen |
| the values are visible on the final page | ✅ | all 12 values found |
| the app reached the state the recording ended in | ✅ | matched the expected end state |
| the app stored exactly the rows we sent | ✅ | 2/2 rows stored as sent |
| the task was submitted | ✅ | 2 record(s) confirmed by the app |

After the replay: `proof_attempt2.png`

## Attempts

### Attempt 1 — failed
- ❌ the app stored exactly the rows we sent: sent 2 row(s), the app holds 1

### Attempt 2 — passed

## Cost

| what | calls | tokens in | cached | tokens out | $ |
|---|---|---|---|---|---|
| intake | 1 | 2,812 | 316 | 1,788 | 0.00114 |
| repair | 1 | 2,122 | 756 | 4,490 | 0.00238 |

Raw per-call trace: `results/submission/intake/ledger.jsonl`

