# rote report — intake.mp4

- **3 attempt(s)**, last replay **passed**
- **$0.02477** over 3 model calls (7,052 in / 48,939 out, 60% cached)
- wall time 109s
- proof data: fresh — never in the recording

## What it understood

**Goal.** Log goods received against a purchase order on the Parts intake page by adding one intake line per item and submitting the intake.

**Success looks like.** Each added line appears in the table below the form with its SKU, description, quantity, unit cost, supplier and location, and after submitting a green confirmation toast appears at the bottom right stating 'Intake submitted — 2 line recorded.'

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

After the replay: `proof_attempt3.png`

## Attempts

### Attempt 1 — failed
- ❌ the app stored exactly the rows we sent: sent 2 row(s), the app holds 1

### Attempt 2 — failed
- ❌ the app stored exactly the rows we sent: sent 2 row(s), the app holds 1

### Attempt 3 — passed

## Cost

| what | calls | tokens in | cached | tokens out | $ |
|---|---|---|---|---|---|
| intake | 1 | 2,812 | 2,748 | 2,514 | 0.00127 |
| repair | 2 | 4,240 | 1,512 | 46,425 | 0.02349 |

Raw per-call trace: `results/submission/intake/ledger.jsonl`

