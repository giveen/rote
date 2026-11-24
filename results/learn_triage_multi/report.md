# rote report — triage.mp4

- **2 attempt(s)**, last replay **passed**
- **$0.00375** over 2 model calls (3,932 in / 7,180 out, 63% cached)
- wall time 21s
- proof data: fresh — never in the recording

## What it understood

**Goal.** Find ticket T-1042 in Open tickets, mark it Resolved with Priority Low, Assignee Jeremy, and resolution note 'Refunded the duplicate charge', then save it.

**Success looks like.** A 'T-1042 saved' confirmation appears at the bottom right, the ticket detail pane closes, and the filtered ticket row shows Priority Low and Status Resolved instead of High and Open.

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
| script runs on fresh data | ✅ | 2 row(s) through triage.py |
| the loop completed one cycle per row | ✅ | 2 iterations, each ending on triage.html |
| every value was accepted by its control | ✅ | all 10 values were typed and confirmed on screen |
| the values are visible on the final page | ✅ | not applicable: this app ends on a screen that does not echo the data, and the end state matches the recording |
| the app reached the state the recording ended in | ✅ | matched the expected end state |
| the app stored exactly the rows we sent | ✅ | 2/2 rows stored as sent |
| the task was submitted | ✅ | 2 record(s) confirmed by the app |
| the repeating block commits each row | ✅ | 2 committing step(s) inside steps 1–7 |

After the replay: `proof_attempt2.png`

## Attempts

### Attempt 1 — failed
```
KeyError: "row has no value for 'ticket_id': ['assignee', 'note', 'priority', 'status', 'ticket']"
```
- ❌ script runs on fresh data: KeyError: "row has no value for 'ticket_id': ['assignee', 'note', 'priority', 'status', 'ticket']"
- ❌ the loop completed one cycle per row: 0 iteration(s) recorded for 2 row(s)
- ❌ every value was accepted by its control: at least one control rejected what was typed
- ❌ the repeating block commits each row: steps 1–1 only enter data, with no click or submit, so 2 rows would overwrite the same form and produce one result instead of 2

### Attempt 2 — passed

## Cost

| what | calls | tokens in | cached | tokens out | $ |
|---|---|---|---|---|---|
| triage | 1 | 1,820 | 1,724 | 2,900 | 0.00147 |
| repair | 1 | 2,112 | 756 | 4,280 | 0.00228 |

Raw per-call trace: `results/learn_triage_multi/ledger.jsonl`

