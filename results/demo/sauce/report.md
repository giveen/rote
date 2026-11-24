# rote report — sauce.mp4

- **3 attempt(s)**, last replay **passed**
- **$0.00775** over 3 model calls (6,611 in / 14,800 out, 49% cached)
- wall time 39s
- proof data: fresh — never in the recording

## What it understood

**Goal.** Log in as standard_user, add Sauce Labs Backpack to the cart, checkout with the entered name and zip code, and complete the order.

**Success looks like.** After the final row's Finish shows Checkout: Complete with 'Thank you for your order!', Back Home returns to the Swag Labs inventory page showing Sauce Labs Backpack ($29.99) and other products, with an empty cart, ready for the next row; each order before returning home is complete with Price Total $32.39, Payment Information SauceCard #31337, and Shipping Information Free Pony Express Delivery!.

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
| 12 | click | Back Home | `` | each_row |

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
  "zip_postal_code": "24037"
 }
]
```

## Proof

| check | result | detail |
|---|---|---|
| script runs on fresh data | ✅ | 3 row(s) through sauce.py |
| the loop completed one cycle per row | ✅ | 3 iterations, each ending on inventory.html |
| every value was accepted by its control | ✅ | all 9 values were typed and confirmed on screen |
| the values are visible on the final page | ✅ | not applicable: this app ends on a screen that does not echo the data, and the end state matches the recording |
| the app reached the state the recording ended in | ✅ | matched the expected end state |
| the repeating block commits each row | ✅ | 6 committing step(s) inside steps 4–12 |

After the replay: `proof_attempt3.png`

## Attempts

### Attempt 1 — failed
```
KeyError: "row has no value for 'username': ['first_name', 'last_name', 'zip_postal_code']"
```
- ❌ script runs on fresh data: KeyError: "row has no value for 'username': ['first_name', 'last_name', 'zip_postal_code']"
- ❌ the loop completed one cycle per row: 0 iteration(s) recorded for 3 row(s)
- ❌ every value was accepted by its control: at least one control rejected what was typed
- ❌ the values are visible on the final page: missing: row 1 first_name='Grace', row 1 last_name='Hopper', row 1 zip_postal_code='20850', row 2 first_name='Katherine', row 2 last_name='Johnson', row 2 zip_postal_code='24740'
- ❌ the app reached the state the recording ended in: expected something like "Checkout: Complete page is shown with a green check, 'Thank you for your order!', order dispatched message, Payment Info"
- ❌ the repeating block commits each row: steps 1–1 only enter data, with no click or submit, so 3 rows would overwrite the same form and produce one result instead of 3

### Attempt 2 — failed
```
LookupError: none of these appeared within 4000ms: [<Locator frame=<Frame name= url='https://www.saucedemo.com/checkout-complete.html'> selector='internal:role=button[name="Add to cart"i]'>, <Locator frame=<Frame name= url='https://www.saucedemo.com/checkout-complete.html'> selector='internal:role=link[name="Add to cart"i]'>, <Locator frame=<Frame name= url='https://www.saucedemo.com/checkout-complete.html'> selector='internal:role=menuitem[name="Add to cart"i]'>, <Locator frame=<Frame name= url='https://www.saucedemo.com/checkout-complete.html'> selector='internal:role=tab[name="Add to cart"i
```
- ❌ script runs on fresh data: LookupError: none of these appeared within 4000ms: [<Locator frame=<Frame name= url='https://www.saucedemo.com/checkout-complete.html'> selector='internal:role=button[name="Add to cart"i]'>, <Locator frame=<Frame name= url='https://www.saucedemo.com/checkout-complete.html'> selector='internal:role=l
- ❌ the loop completed one cycle per row: 1 iteration(s) recorded for 3 row(s)
- ❌ every value was accepted by its control: at least one control rejected what was typed

### Attempt 3 — passed

## Cost

| what | calls | tokens in | cached | tokens out | $ |
|---|---|---|---|---|---|
| sauce | 1 | 1,820 | 1,724 | 3,931 | 0.00198 |
| repair | 2 | 4,791 | 1,512 | 10,869 | 0.00577 |

Raw per-call trace: `results/demo/sauce/ledger.jsonl`

