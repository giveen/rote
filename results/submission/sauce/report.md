# rote report — sauce.mp4

- **2 attempt(s)**, last replay **passed**
- **$0.00957** over 2 model calls (3,957 in / 18,822 out, 63% cached)
- wall time 45s
- proof data: fresh — never in the recording

## What it understood

**Goal.** Log in, add the Sauce Labs Backpack to the cart, and proceed through checkout to the order overview page.

**Success looks like.** The Checkout: Overview page is shown listing Sauce Labs Backpack ($29.99), Payment Information: SauceCard #31337, Shipping Information: Free Pony Express Delivery, and Price Total: $32.39 (Item total: $29.99, Tax: $2.40, Total: $32.39), with Cancel and Finish buttons visible.

| step | action | target | value | scope |
|---|---|---|---|---|
| 1 | type | Username | `standard_user` | once |
| 2 | type | Password | `secret_sauce` | once |
| 3 | click | Login | `` | once |
| 4 | click | Add to cart | `` | once |
| 5 | click | Cart | `` | once |
| 6 | click | Checkout | `` | once |
| 7 | type | First Name | `{first_name}` | each_row |
| 8 | type | Last Name | `{last_name}` | each_row |
| 9 | type | Zip/Postal Code | `{zip_postal_code}` | each_row |
| 10 | click | Continue | `` | each_row |
| 11 | read | Checkout: Overview | `` | each_row |

**Controls found:**
`First Name` (text), `Last Name` (text), `Zip/Postal Code` (text)

**Example rows from the recording:**

```json
[
 {
  "first_name": "Ada",
  "last_name": "Lovelace",
  "zip_postal_code": "21037"
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
- ❌ the app reached the state the recording ended in: expected something like 'The Checkout: Overview page is shown listing Sauce Labs Backpack ($29.99), Payment Information: SauceCard #31337, Shippi'

### Attempt 2 — passed

## Cost

| what | calls | tokens in | cached | tokens out | $ |
|---|---|---|---|---|---|
| sauce | 1 | 1,820 | 1,724 | 8,570 | 0.00430 |
| repair | 1 | 2,137 | 756 | 10,252 | 0.00527 |

Raw per-call trace: `results/submission/sauce/ledger.jsonl`

