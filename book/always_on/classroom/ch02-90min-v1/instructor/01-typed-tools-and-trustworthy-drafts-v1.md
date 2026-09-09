# INSTRUCTOR ANSWERS — do not distribute as the student notebook
This copy replaces the four exercise starters with worked answers. Retain student attempts before showing it. The final instructor checks include additional inputs not in the student feedback tables.

# Chapter 2 · 1. From a model request to a trustworthy draft

**45 minutes · Student classroom edition · 9 September 2026**

Companion to [Give the agent reliable shop tools](https://www.profrod.ai/book/ch02-shop-tools).
You need Python functions, dictionaries, exceptions and basic classes. No model key, supplier
account, repository clone or paid service is used. The only additional package is Pydantic 2.

**Before class:** open in Jupyter or Colab and run the setup cell. If Pydantic 2 is absent,
run `%pip install "pydantic==2.13.4"` in a separate cell, restart the kernel, then Run All.
That one installation needs internet. The lesson itself runs locally without network calls.

Predict each marked result before execution. Exercise starters intentionally print NEEDS_WORK;
that is different from a broken notebook. Edit the exercise cell and rerun its feedback cells.
Keep your first prediction and explain why it changed. Running supplied examples
is not an assessment pass.

```python
import copy
import json
import sys
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

minimum_python = (3, 10)
if sys.version_info[:2] < minimum_python:
    raise RuntimeError("This classroom edition requires Python 3.10 or newer.")
try:
    import pydantic
    from pydantic import BaseModel, ConfigDict, Field, ValidationError
except ImportError as error:
    raise RuntimeError('Run %pip install "pydantic==2.13.4", then restart the kernel.') from error
if pydantic.__version__.split(".")[0] != "2":
    raise RuntimeError('Run %pip install "pydantic==2.13.4", then restart the kernel.')
print("Python", sys.version.split()[0], "| Pydantic", pydantic.__version__)```

## 0–5 min · The problem is a boundary

Lucy has **2 tubs of vanilla**, wants **8**, and pays **250 pence per tub**.
The required quantity is `max(0, target - on_hand) = 6`; the draft total is `6 × 250 = 1500` pence.
The model may propose an operation, but the shop records own stock and price.

Write your predictions before running anything:

| Proposed quantity | Accept or refuse? | Which rule decides? |
|---|---|---|
| `6` | ? | ? |
| `"6"` | ? | ? |
| `True` | ? | ? |
| `7` | ? | ? |

Our path today is **request → typed arguments → business calculation → draft**.
A successful draft says nothing about payment, purchase or delivery.

```python
SHOP = {
    "customer": "Lucy",
    "currency": "GBP",
    "products": [
        {"sku": "SKU-VANILLA", "name": "Vanilla", "on_hand": 2, "reorder_point": 8},
        {"sku": "SKU-CHOCOLATE", "name": "Chocolate", "on_hand": 12, "reorder_point": 6},
        {"sku": "SKU-STRAWBERRY", "name": "Strawberry", "on_hand": 1, "reorder_point": 5},
    ],
}
PRICES = {"SKU-VANILLA": 250, "SKU-CHOCOLATE": 300, "SKU-STRAWBERRY": 275}
products = {row["sku"]: copy.deepcopy(row) for row in SHOP["products"]}
for row in SHOP["products"]:
    print(row["sku"], "need =", max(0, row["reorder_point"] - row["on_hand"]))```

## 5–10 min · Why ordinary Python types need an explicit boundary

Python permits useful operations that would be wrong for this business contract.
Predict the two expressions, then inspect the actual value and type. Does `isinstance` express
the exact integer contract we need?

```python
print("string multiplication:", repr("6" * 3))
print("boolean arithmetic:", True * 250)
print("isinstance(True, int):", isinstance(True, int))
quantity = True
print("type(quantity) is int:", type(quantity) is int)


class ConvenientArguments(BaseModel):
    quantity: int


print("coerced string:", ConvenientArguments.model_validate({"quantity": "6"}).quantity)```

Coercion can be convenient in a form, but here it would erase evidence about what the caller
actually sent. We require an exact integer, a positive bounded quantity,
and no undeclared fields.
Notice that these rules still cannot tell us whether six or seven agrees with Lucy's stock.

## 10–18 min · Exercise 1: construct the argument contract

Edit the class below. Its contract is:

* `sku`: a string of 1–100 characters;
* `quantity`: a strict integer from 1 through 1000;
* reject all undeclared fields, including a caller-supplied `approved` flag.

Pydantic's building blocks are `ConfigDict`, `Field`, `extra="forbid"` and `strict=True`.
Do not add a special case for the example SKU: identity membership belongs to a later boundary.

```python
class StudentDraftArguments(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    sku: str = Field(min_length=1, max_length=100)
    quantity: int = Field(gt=0, le=1000)```

```python
argument_cases = [
    ("six", {"sku": "SKU-VANILLA", "quantity": 6}, True),
    ("boolean", {"sku": "SKU-VANILLA", "quantity": True}, False),
    ("text", {"sku": "SKU-VANILLA", "quantity": "6"}, False),
    ("float", {"sku": "SKU-VANILLA", "quantity": 6.0}, False),
    ("zero", {"sku": "SKU-VANILLA", "quantity": 0}, False),
    ("upper end", {"sku": "SKU-VANILLA", "quantity": 1000}, True),
    ("over limit", {"sku": "SKU-VANILLA", "quantity": 1001}, False),
    ("empty SKU", {"sku": "", "quantity": 6}, False),
    ("long SKU", {"sku": "x" * 101, "quantity": 6}, False),
    ("forged approval", {"sku": "SKU-VANILLA", "quantity": 6, "approved": True}, False),
]
schema_results = []
for label, payload, expected in argument_cases:
    try:
        StudentDraftArguments.model_validate(payload)
        accepted = True
    except ValidationError:
        accepted = False
    schema_results.append(accepted == expected)
    print("PASS" if accepted == expected else "NEEDS_WORK", label, "accepted =", accepted)
print("Exercise 1:", sum(schema_results), "/", len(schema_results))```

<details><summary>Hint 1: where strictness belongs</summary>
Put the configuration on the model class so every field uses the same input policy.
</details>
<details><summary>Hint 2: field bounds</summary>
`min_length`/`max_length` constrain text; `gt`/`le` constrain integer values.
A type annotation alone does not impose these bounds.
</details>

**Pair check:** should a perfectly formatted but unknown SKU pass this schema? Explain why.
The next examples use the book's reference models explicitly, so an unfinished Exercise 1 does
not prevent exploring the business layer. Your Exercise 1 result remains separate.

```python
class NoArguments(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class ProductArguments(NoArguments):
    sku: str = Field(min_length=1, max_length=100)


class DraftArguments(ProductArguments):
    quantity: int = Field(gt=0, le=1000)```

```python
valid_but_wrong = DraftArguments.model_validate({"sku": "SKU-VANILLA", "quantity": 7})
print("Schema accepted:", valid_but_wrong.model_dump())
print(
    "Actual shop need:",
    max(
        0, products[valid_but_wrong.sku]["reorder_point"] - products[valid_but_wrong.sku]["on_hand"]
    ),
)```

## 18–30 min · Exercise 2: make the business rule executable

Implement `student_draft(args, rows, prices)`. `args` has already passed `DraftArguments`.
Stock rows and prices are trusted classroom fixtures. The function must:

1. Find the requested product and compute its current need.
2. Refuse a quantity different from that need with `ValueError`.
3. Obtain the price from `prices`, never from the model request.
4. Return exactly `sku`, `quantity`, `unit_cost_pence`, `total_pence`, and `status="DRAFT"`.
5. Preserve the inputs. Unknown products and absent prices must raise `KeyError`.

Why integer pence? Multiplication stays exact. We do not need binary floating-point pounds or
rounding inside this chapter's pricing rule. Currency conversion and fractional-unit pricing
would require an explicitly different contract.

```python
def student_draft(args, rows, prices):
    row = rows[args.sku]
    needed = max(0, row["reorder_point"] - row["on_hand"])
    if args.quantity != needed:
        raise ValueError("quantity differs from the replenishment need")
    unit_pence = prices[args.sku]
    return {
        "sku": args.sku,
        "quantity": args.quantity,
        "unit_cost_pence": unit_pence,
        "total_pence": args.quantity * unit_pence,
        "status": "DRAFT",
    }```

```python
def check_cases(candidate, cases):
    """Visible teaching feedback; expected values are supplied independently."""
    results = []
    for label, args, expected in cases:
        supplied = copy.deepcopy(args)
        before = copy.deepcopy(supplied)
        try:
            actual = candidate(*supplied)
        except NotImplementedError:
            actual = "NOT_IMPLEMENTED"
        except Exception as error:
            actual = {"raised": type(error).__name__}
        passed = actual == expected and supplied == before
        results.append(passed)
        print(
            "PASS" if passed else "NEEDS_WORK",
            label,
            "| expected:",
            expected,
            "| observed:",
            actual,
        )
        if supplied != before:
            print("  Input mutation detected.")
    print(f"{sum(results)}/{len(results)} visible checks passed")
    return results```

```python
def draft_case(payload, rows, prices):
    args = DraftArguments.model_validate(payload)
    return student_draft(args, rows, prices)


draft_cases = [
    (
        "vanilla six",
        [{"sku": "SKU-VANILLA", "quantity": 6}, products, PRICES],
        {
            "sku": "SKU-VANILLA",
            "quantity": 6,
            "unit_cost_pence": 250,
            "total_pence": 1500,
            "status": "DRAFT",
        },
    ),
    (
        "over-order seven",
        [{"sku": "SKU-VANILLA", "quantity": 7}, products, PRICES],
        {"raised": "ValueError"},
    ),
    (
        "strawberry four",
        [{"sku": "SKU-STRAWBERRY", "quantity": 4}, products, PRICES],
        {
            "sku": "SKU-STRAWBERRY",
            "quantity": 4,
            "unit_cost_pence": 275,
            "total_pence": 1100,
            "status": "DRAFT",
        },
    ),
    (
        "missing SKU",
        [{"sku": "SKU-MISSING", "quantity": 1}, products, PRICES],
        {"raised": "KeyError"},
    ),
    (
        "missing price",
        [{"sku": "SKU-VANILLA", "quantity": 6}, products, {}],
        {"raised": "KeyError"},
    ),
]
draft_results = check_cases(draft_case, draft_cases)```

<details><summary>Hint 1: do not trust the requested quantity</summary>
Calculate the need from the selected row first, then compare the request with that value.
</details>
<details><summary>Hint 2: keep the result grounded</summary>
Look up the unit price by SKU and multiply by the validated quantity. Do not insert a literal total.
</details>

## 30–38 min · Turn your function into a tool

A tool has a name, a description, an argument schema and an executable handler. A JSON schema
describes inputs; it cannot execute Python. The registry will bind the public name to the handler.
Below is the actual `ExecutableTool` class from Chapter 2,
followed by a wrapper around **your** function.

```python
@dataclass(frozen=True)
class ExecutableTool:
    name: str
    description: str
    arguments: type[BaseModel]
    handler: Callable[[Any], Any]
    consequential: bool = False

    def schema(self):
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.arguments.model_json_schema(),
            },
        }```

```python
student_tool = ExecutableTool(
    "draft_order",
    "Calculate a draft using authoritative shop records; never purchases.",
    DraftArguments,
    lambda args: student_draft(args, products, PRICES),
)
schema = student_tool.schema()
print(json.dumps(schema, indent=2))
print("Model-visible argument names:", sorted(schema["function"]["parameters"]["properties"]))```

Find `additionalProperties`, the integer bounds, and `required` in the printed schema.
There is no `unit_cost_pence` input. Now trace the request through the schema and into your handler.
If Exercise 2 is unfinished, the connection should remain unfinished too.

```python
payload = {"sku": "SKU-VANILLA", "quantity": 6}
typed = student_tool.arguments.model_validate(payload, strict=True)
try:
    connected_draft = student_tool.handler(typed)
    print("YOUR CONNECTED TOOL:", connected_draft)
except NotImplementedError:
    connected_draft = None
    print("NEEDS_WORK: complete Exercise 2, then rerun this connection.")
print("Physical stock remains:", products["SKU-VANILLA"]["on_hand"])```

## 38–43 min · Transfer: change the data, keep the mechanism

Mango has one tub, target five, and price 325 pence. Predict the correct quantity and total before
running. Then change only its price to 350. The same handler should produce a different total.
This tests whether your code computes a result or recognizes an example.

```python
mango_rows = {"SKU-MANGO": {"sku": "SKU-MANGO", "on_hand": 1, "reorder_point": 5}}
transfer_cases = [
    (
        "mango 325p",
        [{"sku": "SKU-MANGO", "quantity": 4}, mango_rows, {"SKU-MANGO": 325}],
        {
            "sku": "SKU-MANGO",
            "quantity": 4,
            "unit_cost_pence": 325,
            "total_pence": 1300,
            "status": "DRAFT",
        },
    ),
    (
        "mango 350p",
        [{"sku": "SKU-MANGO", "quantity": 4}, mango_rows, {"SKU-MANGO": 350}],
        {
            "sku": "SKU-MANGO",
            "quantity": 4,
            "unit_cost_pence": 350,
            "total_pence": 1400,
            "status": "DRAFT",
        },
    ),
    (
        "under-order",
        [{"sku": "SKU-MANGO", "quantity": 3}, mango_rows, {"SKU-MANGO": 350}],
        {"raised": "ValueError"},
    ),
]
transfer_results = check_cases(draft_case, transfer_cases)```

## 43–45 min · Retrieval checkpoint

Without looking back, explain:

1. Why can `7` pass the schema and still fail the operation?
2. Where do the unit price and total come from?
3. What is the difference between describing a tool and invoking it?
4. Which observed state proves this example did not change inventory?

Save your edited notebook. Open Notebook 2 next; it has its own setup and does not require
copying a handoff file. The repository's longer successor units remain follow-on practice.

```python
lesson_one_report = {
    "schema_visible": sum(schema_results),
    "schema_total": len(schema_results),
    "draft_visible": sum(draft_results),
    "draft_total": len(draft_results),
    "transfer_visible": sum(transfer_results),
    "transfer_total": len(transfer_results),
    "connected": connected_draft is not None,
    "explanations": "TEACHER_REVIEW_REQUIRED",
}
print(json.dumps(lesson_one_report, indent=2))```

## Instructor-only transfer checks
Do not reveal these before the learner attempt.

```python
assert all(schema_results) and all(draft_results) and all(transfer_results)
assert connected_draft["total_pence"] == 1500
assert products["SKU-VANILLA"]["on_hand"] == 2
pear = {"SKU-PEAR": {"sku": "SKU-PEAR", "on_hand": 2, "reorder_point": 9}}
assert (
    student_draft(DraftArguments(sku="SKU-PEAR", quantity=7), pear, {"SKU-PEAR": 175})[
        "total_pence"
    ]
    == 1225
)
print("INSTRUCTOR CHECKS: notebook 1 passed")```
