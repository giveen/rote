# rote report — vendors.mp4

- **3 attempt(s)**, last replay **passed**
- **$0.02046** over 3 model calls (6,337 in / 40,270 out, 51% cached)
- wall time 87s
- proof data: fresh — never in the recording

## What it understood

**Goal.** Create a new vendor by onboarding a supplier before the first purchase order.

**Success looks like.** A banner reading 'Vendor created and welcome pack queued.' appears above the New vendor form, and the CREATED panel on the right replaces 'No vendors created yet in this session.' with the new vendor's company name, country, contract start shown as 2026-03-01, annual spend, category, reference, notes, and welcome pack status.

| step | action | target | value | scope |
|---|---|---|---|---|
| 1 | type | Company name | `{company_name}` | each_row |
| 2 | select | Country | `{country}` | each_row |
| 3 | type | Contract start | `{contract_start}` | each_row |
| 4 | type | Annual spend | `{annual_spend}` | each_row |
| 5 | select | Category | `{category}` | each_row |
| 6 | type | Internal reference | `{internal_reference}` | each_row |
| 7 | type | Notes | `{notes}` | each_row |
| 8 | check | Send welcome pack | `{send_welcome_pack}` | each_row |
| 9 | submit | Create vendor | `` | once |

**Controls found:**
`Company name` (text), `Country` (select), `Contract start` (text), `Annual spend` (number), `Category` (select), `Internal reference` (text), `Notes` (text), `Send welcome pack` (checkbox)

**Example rows from the recording:**

```json
[
 {
  "company_name": "Nordlicht Logistik GmbH",
  "country": "Germany",
  "contract_start": "03/01/2026",
  "annual_spend": "420000",
  "category": "Logistics",
  "internal_reference": "VD-2041",
  "notes": "Preferred carrier for the northern region.",
  "send_welcome_pack": "yes"
 }
]
```

## Proof

| check | result | detail |
|---|---|---|
| script runs on fresh data | ✅ | 1 row(s) through vendors.py |
| every value was accepted by its control | ✅ | all 8 values were typed and confirmed on screen |
| the values are visible on the final page | ✅ | all 8 values found |
| the app reached the state the recording ended in | ✅ | matched the expected end state |
| the app stored exactly the rows we sent | ✅ | 1/1 rows stored as sent |
| the task was submitted | ✅ | 1 record(s) confirmed by the app |

After the replay: `proof_attempt3.png`

## Attempts

### Attempt 1 — failed
- ❌ the app stored exactly the rows we sent: 0/1 rows stored as sent

### Attempt 2 — failed
- ❌ the app stored exactly the rows we sent: 0/1 rows stored as sent

### Attempt 3 — passed

## Cost

| what | calls | tokens in | cached | tokens out | $ |
|---|---|---|---|---|---|
| vendors | 1 | 1,820 | 1,724 | 4,446 | 0.00224 |
| repair | 2 | 4,517 | 1,512 | 35,824 | 0.01822 |

Raw per-call trace: `results/demo/vendors/ledger.jsonl`

