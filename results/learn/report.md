# rote report — intake.mp4

- **1 attempt(s)**, last replay **passed**
- **$0.00112** over 1 model calls (2,756 in / 2,204 out, 96% cached)
- wall time 9s
- proof data: fresh — never in the recording

## What it understood

**Goal.** Log goods received against a purchase order on the Parts intake page by entering one or more part lines and submitting the intake.

**Success looks like.** Each entered line appears as a row in the table below the form (SKU, Description, QTY, Unit cost, Supplier, Location) and the form resets to its placeholders; after submitting, a confirmation toast appears at the bottom right stating 'Intake submitted — 1 line recorded.'

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
| every value reached the page | ✅ | all 12 values found |
| the app stored exactly the rows we sent | ✅ | 2/2 rows stored as sent |
| the task was submitted | ✅ | 2 line(s) confirmed by the app |

After the replay: `proof_attempt1.png`

## Attempts

### Attempt 1 — passed

## Cost

| what | calls | tokens in | cached | tokens out | $ |
|---|---|---|---|---|---|
| intake | 1 | 2,756 | 2,659 | 2,204 | 0.00112 |

Raw per-call trace: `results/learn/ledger.jsonl`

