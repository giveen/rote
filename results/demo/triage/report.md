# rote report — triage.mp4

- **3 attempt(s)**, last replay **passed**
- **$0.01229** over 3 model calls (6,421 in / 23,586 out, 24% cached)
- wall time 56s
- proof data: fresh — never in the recording

## What it understood

**Goal.** Search for ticket T-1042, open it, set Status to Resolved, Priority to Low, and Assignee to Jeremy, add a resolution note, and save the ticket.

**Success looks like.** The Open tickets list shows T-1042 with Priority Low and Status Resolved, the right panel returns to Nothing open, and a T-1042 saved confirmation appears at the bottom right.

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

After the replay: `proof_attempt3.png`

## Attempts

### Attempt 1 — failed
```
KeyError: "row has no value for 'ticket_id': ['assignee', 'note', 'priority', 'status', 'ticket']"
```
- ❌ script runs on fresh data: KeyError: "row has no value for 'ticket_id': ['assignee', 'note', 'priority', 'status', 'ticket']"
- ❌ the loop completed one cycle per row: 0 iteration(s) recorded for 2 row(s)
- ❌ every value was accepted by its control: at least one control rejected what was typed
- ❌ the repeating block commits each row: steps 1–1 only enter data, with no click or submit, so 2 rows would overwrite the same form and produce one result instead of 2

### Attempt 2 — failed
```
LookupError: none of these appeared within 4000ms: [<Locator frame=<Frame name= url='http://127.0.0.1:8765/triage.html'> selector='internal:role=button[name="Open {ticket}"i]'>, <Locator frame=<Frame name= url='http://127.0.0.1:8765/triage.html'> selector='internal:role=link[name="Open {ticket}"i]'>, <Locator frame=<Frame name= url='http://127.0.0.1:8765/triage.html'> selector='internal:role=menuitem[name="Open {ticket}"i]'>, <Locator frame=<Frame name= url='http://127.0.0.1:8765/triage.html'> selector='internal:role=tab[name="Open {ticket}"i]'>, <Locator frame=<Frame name= url='http://127.0.0
```
- ❌ script runs on fresh data: LookupError: none of these appeared within 4000ms: [<Locator frame=<Frame name= url='http://127.0.0.1:8765/triage.html'> selector='internal:role=button[name="Open {ticket}"i]'>, <Locator frame=<Frame name= url='http://127.0.0.1:8765/triage.html'> selector='internal:role=link[name="Open {ticket}"i]'>
- ❌ the loop completed one cycle per row: 0 iteration(s) recorded for 2 row(s)
- ❌ every value was accepted by its control: at least one control rejected what was typed

### Attempt 3 — passed

## Cost

| what | calls | tokens in | cached | tokens out | $ |
|---|---|---|---|---|---|
| triage | 1 | 1,820 | 0 | 2,947 | 0.00166 |
| repair | 2 | 4,601 | 1,512 | 20,639 | 0.01063 |

Raw per-call trace: `results/demo/triage/ledger.jsonl`

