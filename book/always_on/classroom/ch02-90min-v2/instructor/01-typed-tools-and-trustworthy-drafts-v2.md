# INSTRUCTOR ANSWERS — do not distribute as the student notebook
This copy replaces the four exercise starters with worked answers. Retain student attempts before showing it. The final instructor checks include additional inputs not in the student feedback tables.

# Chapter 2 · 1. From a model request to a trustworthy draft

**50 minutes · Student classroom edition · 9 September 2026**

Companion to [Give the agent reliable shop tools](https://www.profrod.ai/book/ch02-shop-tools).
You need Python functions, dictionaries, exceptions and basic classes. No model key, supplier
account, repository clone or paid service is used. The only additional package is Pydantic 2. No Pydantic experience is assumed; the introduction below teaches it from the beginning.

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

## 0–2 min · The problem is a boundary

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

## Pydantic from first principles · 20-minute guided introduction

**No previous Pydantic experience is assumed.** We start with familiar Python dictionaries,
then build a small contract, inspect failures, and connect that contract to a tool call.
Pydantic is a Python library for checking data against declared types and constraints.
Here, **model** means a class describing data; it is not a neural network or language model.

By the end, you should be able to define a model, validate a dictionary, explain a validation
error, reject unwanted conversions, and distinguish a schema from a business rule.
For the full 90-minute class, learn this introduction in notebook 1 and use its identical copy
in notebook 2 as a reference. Starting notebook 2 on its own takes about 60 minutes including
this introduction; the subsequent core activities take 40 minutes.

### 1. Why annotations alone are not a boundary · minutes 0–2

A caller sends a quantity as a string. A type annotation documents what we expect, but Python
does not automatically check that expectation when the function runs. **Predict:** will this
call raise an error, return twelve, or repeat the characters?

```python
def annotated_double(quantity: int) -> int:
    return quantity * 2


incoming_quantity = "6"
observed = annotated_double(incoming_quantity)
print(repr(observed), type(observed).__name__)
assert observed == "66"```

The result is `'66'`, a string. The annotation did not become a runtime guard.
A type checker can flag this example before execution, but external data still needs a runtime
boundary. We will check it **before** passing it to calculations that assume validated input.

### 2. A model is a recipe; an instance holds data · minutes 2–5

Read `class IntroLine(BaseModel)` as “define our data class using Pydantic's validation machinery.”
The indented annotations declare **fields**, the named pieces of data. `sku` and `quantity`
have no defaults and must be supplied. `note` has a default, so callers can omit it.
`str` and `int` are ordinary Python types. No decorators or inheritance theory are needed
to use this pattern: declare the fields inside a class that inherits from `BaseModel`.

The class is the reusable recipe; `line` is one validated instance. The constructor accepts
named arguments. `model_validate` accepts a dictionary, which is convenient when a tool caller
has already produced one. Dot notation reads the instance's fields. **Predict** the missing note.

```python
class IntroLine(BaseModel):
    sku: str
    quantity: int
    note: str = ""


line = IntroLine(sku="SKU-VANILLA", quantity=6)
incoming = {"sku": "SKU-VANILLA", "quantity": 6}
parsed_line = IntroLine.model_validate(incoming)
print(line.sku, line.quantity, repr(line.note))
print("Same values:", line == parsed_line)
assert line.note == "" and line == parsed_line```

### 3. Read an error as a repair instruction · minutes 5–7

Now omit `sku` and supply a quantity that cannot be parsed as an integer. Pydantic raises
`ValidationError` instead of returning a usable instance. Catch this expected exception so
the notebook can show the failure and continue. Its `errors()` method returns structured
details: `loc` identifies the field, `type` classifies the failure, and `msg` explains it.
We hide the raw input in this display; we need the location and rule to understand the failure.

**Predict:** how many fields need repair? A missing required field is different from a field
with an invalid value. Read every reported error, not just the first line.

```python
bad_line = {"quantity": "six"}
try:
    IntroLine.model_validate(bad_line)
except ValidationError as error:
    details = error.errors(include_url=False, include_input=False)
    for detail in details:
        print(detail["loc"], detail["type"], detail["msg"])
    assert {item["loc"] for item in details} == {("sku",), ("quantity",)}
else:
    raise AssertionError("The invalid line was accepted")```

Both fields need attention. An exception is useful feedback here, not a notebook setup
failure. In the tool dispatcher later, this same exception becomes a refused observation.
Validation reports the problem; it does not decide whether to ask the caller to correct it.

### 4. Accepted input can be converted input · minutes 7–10

By default, Pydantic may convert compatible input into the declared type. That is helpful for
a form but can hide what a tool caller actually sent. For an integer field, compare `6`,
`"6"`, `True`, `6.0`, and `"six"`. **Write the two acceptance columns before running.**
The `strict=True` argument asks this validation call to reject these integer conversions.
This table concerns Python inputs to an integer field; strict handling of JSON dates and other
types has additional rules. We do not generalize this table to every type.

```python
class IntroQuantity(BaseModel):
    quantity: int


def inspect_quantity(value, strict):
    try:
        result = IntroQuantity.model_validate({"quantity": value}, strict=strict)
    except ValidationError:
        return "REFUSED"
    return f"{result.quantity!r} ({type(result.quantity).__name__})"


quantity_inputs = [6, "6", True, 6.0, "six"]
for value in quantity_inputs:
    print(
        repr(value),
        "| default:",
        inspect_quantity(value, False),
        "| strict:",
        inspect_quantity(value, True),
    )
assert [inspect_quantity(value, True) != "REFUSED" for value in quantity_inputs] == [
    True,
    False,
    False,
    False,
    False,
]
boolean_quantity = True
print("Python considers bool an int subclass:", isinstance(boolean_quantity, int))
print("Its exact type is int:", type(boolean_quantity) is int)```

Default validation converts the first four values to integers. The strict
column accepts only `6`. Python's boolean/integer relationship explains why a casual
`isinstance(value, int)` check would miss one of these cases. Pydantic's strict integer
validation rejects a boolean. Choose the conversion policy deliberately at the boundary.

### 5. Types, constraints, and model policy do different jobs · minutes 10–13

Our stock-reading contract has three layers:

| Declaration | Meaning in this example |
|---|---|
| `on_hand: int` | The resulting field is an integer |
| `Field(ge=0, le=1000)` | Its value is at least zero and at most 1000 |
| `ConfigDict(strict=True)` | The model uses strict validation by default |
| `ConfigDict(extra="forbid")` | Undeclared keys cause an error |

`ge` means greater than or equal; `gt` means strictly greater. `le` means less than or equal.
For strings, `min_length` and `max_length` constrain character count. Here `Field(...)`
adds constraints; it does not supply a field value. `model_config` configures validation;
it is not an input field. Pydantic otherwise ignores extra keys by default, so we explicitly
forbid them when every accepted argument should belong to the declared contract.

**Predict:** zero tubs is valid stock. Should negative stock, a string count, or an extra
`approved` key pass this contract? The stock example is different from an order, which will
require a positive quantity in Exercise 1.

```python
class IntroStockReading(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")
    sku: str = Field(min_length=1, max_length=100)
    on_hand: int = Field(ge=0, le=1000)


stock_examples = [
    ("empty shelf", {"sku": "SKU-VANILLA", "on_hand": 0}, True),
    ("negative count", {"sku": "SKU-VANILLA", "on_hand": -1}, False),
    ("string count", {"sku": "SKU-VANILLA", "on_hand": "2"}, False),
    ("extra key", {"sku": "SKU-VANILLA", "on_hand": 2, "approved": True}, False),
]
for label, payload, expected in stock_examples:
    try:
        validated = IntroStockReading.model_validate(payload)
        accepted = True
        print(label, "ACCEPTED", validated.model_dump())
    except ValidationError as error:
        accepted = False
        print(label, "REFUSED", [item["type"] for item in error.errors()])
    assert accepted == expected```

### 6. Dictionary, instance, JSON, schema · minutes 13–16

These objects serve different purposes. A dictionary contains Python data. A model instance
provides validated fields. JSON text is a portable string representation. A JSON Schema
describes the expected shape so another program can discover the contract.

| Operation | Input → output | Purpose |
|---|---|---|
| `IntroStockReading.model_validate(data)` | dictionary → instance | Validate Python data |
| `reading.model_dump()` | instance → dictionary | Obtain Python field values |
| `reading.model_dump_json()` | instance → JSON string | Serialize this instance |
| `IntroStockReading.model_validate_json(text)` | JSON string → instance | Parse and validate JSON |
| `IntroStockReading.model_json_schema()` | model class → schema dict | Describe the contract |

For these string/integer fields, the round trip preserves the values. Other field types can
need different serialization choices. The schema below describes **possible stock readings**;
it does not contain the current reading, validate a caller by itself, or execute a handler.
**Predict:** which output contains the actual count, and which contains its minimum?

```python
reading = IntroStockReading(sku="SKU-VANILLA", on_hand=2)
as_dict = reading.model_dump()
as_json = reading.model_dump_json()
schema_description = IntroStockReading.model_json_schema()
print("Dictionary:", as_dict)
print("JSON string:", repr(as_json))
print("Count description:", schema_description["properties"]["on_hand"])
print("Required fields:", schema_description["required"])
assert isinstance(as_dict, dict) and isinstance(as_json, str)
assert IntroStockReading.model_validate_json(as_json) == reading
assert schema_description["properties"]["on_hand"]["minimum"] == 0
assert schema_description["additionalProperties"] is False```

### 7. Validation is a contract check, not a fact check · minutes 16–17

An invented count of 999 satisfies our type and range rules. Pydantic has no connection to
Lucy's shelf and cannot know whether that count is true. We must compare it with an
authoritative source separately. Similarly, validating an `approved` field in some other
schema would not establish that a real person authorized a purchase.

The model also does not promise that ordinary assignments to an existing instance are
revalidated: assignment validation is a separate configuration option. In this lesson we
validate new input at the boundary and then use its fields; we do not use unvalidated updates.

```python
plausible_but_unverified = IntroStockReading(sku="SKU-VANILLA", on_hand=999)
authoritative_count = 2
print("Passes the declared contract:", plausible_but_unverified.on_hand)
print("Matches the shop record:", plausible_but_unverified.on_hand == authoritative_count)
assert plausible_but_unverified.on_hand != authoritative_count```

### 8. Your turn: repair the data without weakening the contract · minutes 17–20

The authoritative record says SKU `SKU-VANILLA` has **2** tubs. Repair `repaired_stock`
in the next cell so it represents that record and passes `IntroStockReading`. Keep the model
unchanged. Before running, name all three problems with the supplied dictionary. Explain
why changing a type annotation to `Any` would hide a problem rather than repair this data.

Hint 1: inspect the required names and each value's Python type.
Hint 2: an empty string is still a string, but the length constraint matters.
Hint 3: the data contract has exactly two fields. A proposed approval is not stock data.

```python
repaired_stock = {"sku": "SKU-VANILLA", "on_hand": 2}```

```python
try:
    repaired_reading = IntroStockReading.model_validate(repaired_stock)
except ValidationError as error:
    pydantic_checkpoint = False
    for detail in error.errors(include_url=False, include_input=False):
        print(detail["loc"], detail["msg"])
else:
    pydantic_checkpoint = repaired_reading.model_dump() == {
        "sku": "SKU-VANILLA",
        "on_hand": 2,
    }
print("PASS" if pydantic_checkpoint else "NEEDS_WORK", "Pydantic data-repair checkpoint")```

### Retrieve the mechanism before continuing

Close the examples and explain: (1) what makes a field required, (2) why `"6"` can pass one
integer model and fail another, (3) what `loc` tells you, (4) how a schema differs from an
instance, and (5) why a valid count can still be false. Use your observed outputs as evidence.

**Vocabulary:** a *field* is one named data item; a *constraint* limits its allowed values;
*coercion* converts input; *validation* checks the declared contract; *serialization* converts
an instance to a representation for storage or transport. None of these grants permission.

**Connection to our shop tools:** `NoArguments` accepts an empty argument dictionary;
`ProductArguments` checks a SKU; `DraftArguments` also checks a positive quantity.
Each follows the same `BaseModel` pattern you have just used. A tool's `parameters` points
to one of these classes. The dispatcher calls `tool.parameters.model_validate(call.arguments)`
before handing the resulting instance to the handler. Later, trace that exact call in the code.
The model owns structural checks; shop records and the handler own the business calculation;
the allowlist and authority callback decide whether execution may proceed.

Official Pydantic 2 references for further reading:
[models](https://docs.pydantic.dev/latest/concepts/models/),
[fields](https://docs.pydantic.dev/latest/concepts/fields/),
[strict mode](https://docs.pydantic.dev/latest/concepts/strict_mode/),
[validation errors](https://docs.pydantic.dev/latest/errors/errors/),
[serialization](https://docs.pydantic.dev/latest/concepts/serialization/), and
[JSON Schema](https://docs.pydantic.dev/latest/concepts/json_schema/).

Coercion can be convenient in a form, but here it would erase evidence about what the caller
actually sent. We require an exact integer, a positive bounded quantity,
and no undeclared fields.
Notice that these rules still cannot tell us whether six or seven agrees with Lucy's stock.

## 22–28 min · Exercise 1: construct the argument contract

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

## 28–40 min · Exercise 2: make the business rule executable

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

## 40–46 min · Turn your function into a tool

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

## 46–48 min · Transfer: change the data, keep the mechanism

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

## 48–50 min · Retrieval checkpoint

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

```python
assert pydantic_checkpoint
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
