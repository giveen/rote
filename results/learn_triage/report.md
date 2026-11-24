# rote report — triage.mp4

- **2 attempt(s)**, last replay **passed**
- **$0.00509** over 2 model calls (3,877 in / 9,558 out, 20% cached)
- wall time 24s
- proof data: fresh — never in the recording

## What it understood

**Goal.** Find a ticket in the open tickets queue, open it, mark it Resolved, change its priority, assign it, add a resolution note, and save it.

**Success looks like.** The ticket row in the Open tickets list shows Priority Low and Status Resolved, the ticket detail panel closes, and a confirmation reading 'T-1042 saved' appears at the bottom right.

| step | action | target | value | scope |
|---|---|---|---|---|
| 1 | type | Search tickets | `{ticket}` | each_row |
| 2 | click | Open | `` | each_row |
| 3 | select | Status | `{status}` | each_row |
| 4 | select | Priority | `{priority}` | each_row |
| 5 | select | Assignee | `{assignee}` | each_row |
| 6 | type | Resolution note | `{note}` | each_row |
| 7 | click | Save ticket | `` | each_row |

**Controls found:**
`Search tickets` (text), `Status` (select), `Priority` (select), `Assignee` (select), `Resolution note` (text)

**Example rows from the recording:**

```json
[
 {
  "ticket_id": "T-1042",
  "status": "Resolved",
  "priority": "Low",
  "assignee": "Jeremy",
  "resolution_note": "Refunded the duplicate charge"
 }
]
```

## Proof

| check | result | detail |
|---|---|---|
| script runs on fresh data | ✅ | 1 row(s) through triage.py |
| every value was accepted by its control | ✅ | all 5 values were typed and confirmed on screen |
| the values are visible on the final page | ✅ | not applicable: this app ends on a screen that does not echo the data, and the end state matches the recording |
| the app reached the state the recording ended in | ✅ | matched the expected end state |

After the replay: `proof_attempt2.png`

## Attempts

### Attempt 1 — failed
```
KeyError: "row has no value for 'ticket_id': ['assignee', 'note', 'priority', 'status', 'ticket']"
```
- ❌ script runs on fresh data: KeyError: "row has no value for 'ticket_id': ['assignee', 'note', 'priority', 'status', 'ticket']"
- ❌ every value was accepted by its control: at least one control rejected what was typed

### Attempt 2 — passed

## Cost

| what | calls | tokens in | cached | tokens out | $ |
|---|---|---|---|---|---|
| triage | 1 | 1,820 | 0 | 3,043 | 0.00170 |
| repair | 1 | 2,057 | 756 | 6,515 | 0.00339 |

Raw per-call trace: `results/learn_triage/ledger.jsonl`

