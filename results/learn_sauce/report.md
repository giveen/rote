# rote report — sauce.mp4

- **3 attempt(s)**, last replay **did not pass**
- **$0.01683** over 3 model calls (5,559 in / 33,185 out, 59% cached)
- wall time 73s
- proof data: fresh — never in the recording

## What it understood

**Goal.** Log in, add the Sauce Labs Backpack to the cart, and complete checkout.

**Success looks like.** The 'Checkout: Complete!' page is displayed with a green checkmark and the message 'Thank you for your order!' and a note that the order has been dispatched.

| step | action | target | value | scope |
|---|---|---|---|---|
| 1 | type | Username | `standard_user` | once |
| 2 | type | Password | `secret_sauce` | once |
| 3 | click | Login | `` | once |
| 4 | click | Sauce Labs Backpack | `` | each_row |
| 5 | click | Add to cart | `` | each_row |
| 6 | click | Cart | `` | each_row |
| 7 | click | Checkout | `` | each_row |
| 8 | type | First Name | `{first_name}` | each_row |
| 9 | type | Last Name | `{last_name}` | each_row |
| 10 | type | Zip/Postal Code | `{zip}` | each_row |
| 11 | click | Continue | `` | each_row |
| 12 | submit | Finish | `` | once |

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
  "zip_postal_code": "21037"
 }
]
```

## Proof

| check | result | detail |
|---|---|---|
| script runs on fresh data | ❌ | LookupError: no button named 'Sauce Labs Backpack' on https://www.saucedemo.com/inventory.html |
| every value reached the page | ❌ | missing: row 1 first_name='Grace', row 1 last_name='Hopper', row 1 zip='20850' |

After the replay: `proof_attempt3.png`

## Attempts

### Attempt 1 — failed
```
KeyError: "row has no value for 'username': ['first_name', 'last_name', 'zip']"
```
- ❌ script runs on fresh data: KeyError: "row has no value for 'username': ['first_name', 'last_name', 'zip']"
- ❌ every value reached the page: missing: row 1 first_name='Grace', row 1 last_name='Hopper', row 1 zip='20850'

### Attempt 2 — failed
```
LookupError: no button named 'Add to cart' on https://www.saucedemo.com/inventory.html
```
- ❌ script runs on fresh data: LookupError: no button named 'Add to cart' on https://www.saucedemo.com/inventory.html
- ❌ every value reached the page: missing: row 1 first_name='Grace', row 1 last_name='Hopper', row 1 zip='20850'

### Attempt 3 — failed
```
LookupError: no button named 'Sauce Labs Backpack' on https://www.saucedemo.com/inventory.html
```
- ❌ script runs on fresh data: LookupError: no button named 'Sauce Labs Backpack' on https://www.saucedemo.com/inventory.html
- ❌ every value reached the page: missing: row 1 first_name='Grace', row 1 last_name='Hopper', row 1 zip='20850'

## Cost

| what | calls | tokens in | cached | tokens out | $ |
|---|---|---|---|---|---|
| sauce | 1 | 1,764 | 1,758 | 4,113 | 0.00206 |
| repair | 2 | 3,795 | 1,512 | 29,072 | 0.01477 |

Raw per-call trace: `results/learn_sauce/ledger.jsonl`

