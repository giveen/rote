# rote report — vendors.mp4

- **3 attempt(s)**, last replay **did not pass**
- **$0.01392** over 3 model calls (5,717 in / 27,233 out, 48% cached)
- wall time 61s
- proof data: fresh — never in the recording

## What it understood

**Goal.** Create a new vendor on the 'New vendor' form, onboarding a supplier before the first purchase order and sending a welcome pack.

**Success looks like.** A green banner 'Vendor created and welcome pack queued.' appears at the top of the New vendor form, and the right-hand CREATED panel changes from 'No vendors created yet in this session.' to show the created vendor's company name, country, contract start (2026-03-01), annual spend, category, internal reference, notes, and welcome pack: yes. The entered form values remain visible.

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
| 9 | click | Create vendor | `` | once |

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
| every value reached the page | ❌ | missing: row 1 send_welcome_pack='true' |

After the replay: `proof_attempt3.png`

## Attempts

### Attempt 1 — failed
- ❌ every value reached the page: missing: row 1 send_welcome_pack='true'

### Attempt 2 — failed
- ❌ every value reached the page: missing: row 1 send_welcome_pack='true'

### Attempt 3 — failed
- ❌ every value reached the page: missing: row 1 send_welcome_pack='true'

## Cost

| what | calls | tokens in | cached | tokens out | $ |
|---|---|---|---|---|---|
| vendors | 1 | 1,764 | 1,758 | 3,586 | 0.00180 |
| repair | 2 | 3,953 | 1,000 | 23,647 | 0.01212 |

Raw per-call trace: `results/learn_vendors/ledger.jsonl`

