# rote report — sauce.mp4

- **2 attempt(s)**, last replay **passed**
- **$0.00461** over 2 model calls (3,808 in / 8,928 out, 65% cached)
- wall time 22s
- proof data: fresh — never in the recording

## What it understood

**Goal.** Log in, add the Sauce Labs Backpack to the cart, and complete checkout with the entered information.

**Success looks like.** Checkout: Complete page displays "Thank you for your order!" for the Sauce Labs Backpack, with Price Total $32.39.

| step | action | target | value | scope |
|---|---|---|---|---|
| 1 | type | Username | `standard_user` | once |
| 2 | type | Password | `secret_sauce` | once |
| 3 | click | Login | `` | once |
| 4 | click | Add to cart | `` | each_row |
| 5 | click | Cart | `` | each_row |
| 6 | click | Checkout | `` | each_row |
| 7 | type | First Name | `{first_name}` | each_row |
| 8 | type | Last Name | `{last_name}` | each_row |
| 9 | type | Zip/Postal Code | `{zip_postal_code}` | each_row |
| 10 | click | Continue | `` | each_row |
| 11 | click | Finish | `` | each_row |

**Controls found:**
`Username` (text), `Password` (text), `First Name` (text), `Last Name` (text), `Zip/Postal Code` (text)

**Example rows from the recording:**

```json
[
 {
  "username": "standard_user",
  "password": "secret_sauce",
  "first_name": "Ada",
  "last_name": "Lovelace",
  "zip_postal_code": "90210"
 }
]
```

## Proof

| check | result | detail |
|---|---|---|
| script runs on fresh data | ✅ | 1 row(s) through sauce.py |
| every value was accepted by its control | ✅ | all 3 values were typed and confirmed on screen |
| the values are visible on the final page | ✅ | not applicable: this app ends on a screen that does not echo the data, and the end state matches the recording |
| the app reached the state the recording ended in | ✅ | matched the expected end state |

After the replay: `proof_attempt2.png`

## Attempts

### Attempt 1 — failed
```
KeyError: "row has no value for 'username': ['first_name', 'last_name', 'zip_postal_code']"
```
- ❌ script runs on fresh data: KeyError: "row has no value for 'username': ['first_name', 'last_name', 'zip_postal_code']"
- ❌ every value was accepted by its control: at least one control rejected what was typed
- ❌ the values are visible on the final page: missing: row 1 first_name='Grace', row 1 last_name='Hopper', row 1 zip_postal_code='20850'
- ❌ the app reached the state the recording ended in: expected something like 'Checkout: Complete page displays "Thank you for your order!" for the Sauce Labs Backpack, with Price Total $32.39.'

### Attempt 2 — passed

## Cost

| what | calls | tokens in | cached | tokens out | $ |
|---|---|---|---|---|---|
| sauce | 1 | 1,820 | 1,724 | 2,901 | 0.00147 |
| repair | 1 | 1,988 | 756 | 6,027 | 0.00314 |

Raw per-call trace: `results/learn_sauce/ledger.jsonl`

