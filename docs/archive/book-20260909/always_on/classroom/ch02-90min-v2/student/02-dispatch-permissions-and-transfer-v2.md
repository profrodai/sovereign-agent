# Chapter 2 · 2. Build the execution boundary and challenge it

**40 minutes · Student classroom edition · 9 September 2026**

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
from types import MappingProxyType
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

## Choose your starting point

**Continuing notebook 1:** retrieve the five primer questions, then jump to
**50–54 min · Reassemble**. The introduction below repeats the same lesson
so this notebook can stand alone. Run All can safely execute its examples.

**Starting here:** work through the 20-minute introduction first, then the
40-minute dispatcher lesson. Clock labels after the primer refer to the full class;
your standalone session takes about 60 minutes before extensions.

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
repaired_stock = {"sku": "", "on_hand": "2", "approved": True}```

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

## 50–54 min · Reassemble the path

This notebook is independently runnable. The supplied models and tool class are reference code
from the book, not credit for Exercise 1. Your work here is repairing dispatch and extending the
stock rule through the connected system.

The dispatcher decides **whether a request may reach its handler**. Trace this path:

`tool name → registry + allowlist → strict arguments → authority check → handler → JSON result`

Which check should reject an unknown name? Which must happen before an effect? Can a schema
advertised to a model enforce permission by itself?

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

```python
class NoArguments(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class ProductArguments(NoArguments):
    sku: str = Field(min_length=1, max_length=100)


class DraftArguments(ProductArguments):
    quantity: int = Field(gt=0, le=1000)


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
        }


class ToolCall(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    id: str = Field(min_length=1, max_length=200)
    name: str = Field(min_length=1, max_length=100, pattern=r"^[a-zA-Z0-9_-]+$")
    arguments: dict[str, Any]```

### Read the actual dispatcher, one boundary at a time

Annotate the code below with the five checks in the path. `MappingProxyType` prevents ordinary
registry assignment; a `frozenset` describes the caller's allowed operations. Neither is a
substitute for checking every invocation.

The final byte limit is checked **after** the handler returns. It limits the returned observation,
not the handler's execution time, memory, or effects. This is trusted local code, not a sandbox.

```python
class Dispatcher:
    def __init__(self, tools, *, allowed, before_write=None, max_result_bytes=16_384):
        self.tools = MappingProxyType({tool.name: tool for tool in tools})
        if len(self.tools) != len(tools):
            raise ValueError("tool names must be unique")
        if not 128 <= max_result_bytes <= 1_048_576:
            raise ValueError("invalid tool result byte limit")
        self.allowed, self.before_write = allowed, before_write
        self.max_result_bytes = max_result_bytes

    def schemas(self):
        return [tool.schema() for name, tool in sorted(self.tools.items()) if name in self.allowed]

    def invoke(self, call):
        tool = self.tools.get(call.name)
        if tool is None or call.name not in self.allowed:
            return {"ok": False, "error": "tool_not_allowed"}
        try:
            arguments = tool.arguments.model_validate(call.arguments, strict=True)
        except ValidationError:
            return {"ok": False, "error": "invalid_arguments"}
        if tool.consequential and self.before_write is None:
            return {"ok": False, "error": "write_authority_required"}
        try:
            if tool.consequential:
                self.before_write(call)
            value = tool.handler(arguments)
            encoded = json.dumps(value, allow_nan=False)
            if len(encoded.encode()) > self.max_result_bytes:
                return {"ok": False, "error": "result_too_large"}
            return {"ok": True, "value": value}
        except (ValueError, TypeError, KeyError, PermissionError, TimeoutError, OSError):
            return {"ok": False, "error": "tool_failed"}```

```python
def build_tools(shop):
    rows = {row["sku"]: copy.deepcopy(row) for row in shop["products"]}
    if len(rows) != len(shop["products"]):
        raise ValueError("duplicate product identity")

    def stock(_):
        return [
            {**row, "needed": max(0, row["reorder_point"] - row["on_hand"])}
            for _, row in sorted(rows.items())
        ]

    def quote(args):
        if args.sku not in rows:
            raise KeyError("unknown product")
        return {
            "sku": args.sku,
            "supplier": "lucy-local",
            "currency": "GBP",
            "unit_cost_pence": PRICES[args.sku],
        }

    def draft(args):
        row = rows[args.sku]
        needed = max(0, row["reorder_point"] - row["on_hand"])
        if args.quantity != needed:
            raise ValueError("quantity differs from the replenishment need")
        price = quote(ProductArguments(sku=args.sku))
        return {
            **price,
            "quantity": args.quantity,
            "total_pence": args.quantity * price["unit_cost_pence"],
            "status": "DRAFT",
        }

    registered = [
        ExecutableTool("list_stock", "Read stock and calculated need.", NoArguments, stock),
        ExecutableTool("supplier", "Read supplier price in GBP pence.", ProductArguments, quote),
        ExecutableTool("draft_order", "Calculate a draft; never purchases.", DraftArguments, draft),
    ]
    return Dispatcher(registered, allowed=frozenset(tool.name for tool in registered))```

```python
reference_shop = build_tools(SHOP)
good_call = ToolCall(id="demo", name="draft_order", arguments={"sku": "SKU-VANILLA", "quantity": 6})
print(reference_shop.invoke(good_call))
assert reference_shop.invoke(good_call)["value"]["total_pence"] == 1500```

## 54–57 min · Distinguish the refusal layers

Before execution, label each request: **name/permission**, **argument schema**,
or **business rule**.
The last two business failures share `tool_failed` externally. A short public error code need
not expose raw input or an arbitrary internal exception message.

```python
requests = [
    ToolCall(id="name", name="run_shell", arguments={}),
    ToolCall(id="type", name="draft_order", arguments={"sku": "SKU-VANILLA", "quantity": True}),
    ToolCall(
        id="extra",
        name="draft_order",
        arguments={"sku": "SKU-VANILLA", "quantity": 6, "approved": True},
    ),
    ToolCall(id="need", name="draft_order", arguments={"sku": "SKU-VANILLA", "quantity": 7}),
    ToolCall(id="sku", name="supplier", arguments={"sku": "UNKNOWN"}),
]
for call in requests:
    print(call.id, reference_shop.invoke(call))```

## 57–68 min · Exercise 3: repair two independent dispatcher defects

The following is a working copy of the chapter's `invoke`, with **two deliberate bugs**.
Repair this cell, then rerun the instrumentation below.

* A tool may be registered but forbidden to this caller. Repair the execution check.
* A refusing authority callback must prevent the handler from running. Repair the order.

Do not change the tests or replace every result with a refusal. A legitimate allowed call must
still execute exactly once. First predict the error response
**and the handler count** for each case.

```python
def student_invoke(self, call):
    tool = self.tools.get(call.name)
    if tool is None:  # BUG A: a registered tool may still be forbidden
        return {"ok": False, "error": "tool_not_allowed"}
    try:
        arguments = tool.arguments.model_validate(call.arguments, strict=True)
    except ValidationError:
        return {"ok": False, "error": "invalid_arguments"}
    if tool.consequential and self.before_write is None:
        return {"ok": False, "error": "write_authority_required"}
    try:
        value = tool.handler(arguments)  # BUG B: inspect the execution order
        if tool.consequential:
            self.before_write(call)
        encoded = json.dumps(value, allow_nan=False)
        if len(encoded.encode()) > self.max_result_bytes:
            return {"ok": False, "error": "result_too_large"}
        return {"ok": True, "value": value}
    except (ValueError, TypeError, KeyError, PermissionError, TimeoutError, OSError):
        return {"ok": False, "error": "tool_failed"}```

```python
class StudentDispatcher(Dispatcher):
    invoke = student_invoke


def dispatch_probe(kind, dispatcher_type=StudentDispatcher):
    events = []

    def handler(_):
        events.append("handler")
        return {"receipt": "LOCAL_PROBE_ONLY"}

    def authority(_):
        events.append("authority")
        if kind == "refused":
            raise PermissionError("no current approval")

    consequential = kind in {"refused", "allowed-write", "missing-authority"}
    tool = ExecutableTool(
        "probe",
        "Harmless local instrumentation.",
        NoArguments,
        handler,
        consequential=consequential,
    )
    allowed = frozenset() if kind == "forbidden" else frozenset({"probe"})
    checker = authority if kind in {"refused", "allowed-write"} else None
    dispatcher = dispatcher_type([tool], allowed=allowed, before_write=checker)
    response = dispatcher.invoke(ToolCall(id=kind, name="probe", arguments={}))
    return {"ok": response["ok"], "error": response.get("error"), "events": events}


dispatch_expected = {
    "forbidden": {"ok": False, "error": "tool_not_allowed", "events": []},
    "refused": {"ok": False, "error": "tool_failed", "events": ["authority"]},
    "allowed-write": {"ok": True, "error": None, "events": ["authority", "handler"]},
    "missing-authority": {"ok": False, "error": "write_authority_required", "events": []},
    "allowed-read": {"ok": True, "error": None, "events": ["handler"]},
}
dispatch_results = []
for kind, expected in dispatch_expected.items():
    actual = dispatch_probe(kind)
    dispatch_results.append(actual == expected)
    print("PASS" if actual == expected else "NEEDS_WORK", kind, actual)
print("Exercise 3:", sum(dispatch_results), "/", len(dispatch_results))```

<details><summary>Hint 1: registry versus permission</summary>
Existence in `self.tools` answers whether the implementation is known. Membership in `self.allowed`
answers whether this caller may invoke it. Both are required.
</details>
<details><summary>Hint 2: an error result can arrive too late</summary>
Find the first line that can call the handler. Any authority callback
that can refuse must run before it.
</details>

**Explain the observation:** in the broken version, the refused call returns an error even though
the handler ran. Why would grading only `response["ok"]` miss the bug?

## 68–71 min · The stock report and the draft can disagree

Lucy now reserves three vanilla tubs for a catering order. Sellable stock is `on_hand - reserved`.
The replenishment rule becomes `max(0, target - on_hand + reserved)`.
For two on hand, target eight and three reserved, the need is **nine**.

Run the old book factory on this new fixture. It still reports six because reservations were
not part of its original contract. Merely adding a data field does not implement new behavior.

```python
reserved_shop = copy.deepcopy(SHOP)
reserved_shop["products"][0]["reserved"] = 3
old = build_tools(reserved_shop)
old_stock = old.invoke(ToolCall(id="old-stock", name="list_stock", arguments={}))
print(
    "Original rule:",
    next(row["needed"] for row in old_stock["value"] if row["sku"] == "SKU-VANILLA"),
)
print(
    "Nine-tub draft:",
    old.invoke(
        ToolCall(id="new-need", name="draft_order", arguments={"sku": "SKU-VANILLA", "quantity": 9})
    ),
)```

## 71–81 min · Exercise 4: one invariant, two call sites

The teaching extension below passes one `need` function to both stock reporting and draft
validation. Follow both uses. This is an explicit extension of the chapter's factory; the
dispatcher and typed contracts remain the actual book definitions.

Implement `student_need`. Inputs are trusted rows with nonnegative integer stock, target and
reservation counts; absent `reserved` means zero. Do not change stock or reserve additional units.
Check an exact-zero result, a surplus, and a reservation greater than current physical stock.

```python
def student_need(row):
    # Exercise 4: account for units already reserved for catering.
    return max(0, row["reorder_point"] - row["on_hand"])```

```python
def build_reserved_tools(shop, prices, need, dispatcher_type=Dispatcher):
    """Teaching extension: inject one shared need rule into both reporting and drafting."""
    rows = {row["sku"]: copy.deepcopy(row) for row in shop["products"]}
    if len(rows) != len(shop["products"]):
        raise ValueError("duplicate product identity")
    saved_prices = copy.deepcopy(prices)

    def stock(_):
        return [{**row, "needed": need(row)} for _, row in sorted(rows.items())]

    def quote(args):
        if args.sku not in rows:
            raise KeyError("unknown product")
        return {
            "sku": args.sku,
            "supplier": "lucy-local",
            "currency": "GBP",
            "unit_cost_pence": saved_prices[args.sku],
        }

    def draft(args):
        if args.quantity != need(rows[args.sku]):
            raise ValueError("quantity differs from current need")
        price = quote(ProductArguments(sku=args.sku))
        return {
            **price,
            "quantity": args.quantity,
            "total_pence": args.quantity * price["unit_cost_pence"],
            "status": "DRAFT",
        }

    tools = [
        ExecutableTool("list_stock", "Read stock and need.", NoArguments, stock),
        ExecutableTool("supplier", "Read price.", ProductArguments, quote),
        ExecutableTool("draft_order", "Calculate a draft.", DraftArguments, draft),
    ]
    return dispatcher_type(tools, allowed=frozenset(tool.name for tool in tools))```

```python
need_cases = [
    ({"on_hand": 2, "reorder_point": 8, "reserved": 3}, 9),
    ({"on_hand": 2, "reorder_point": 8}, 6),
    ({"on_hand": 8, "reorder_point": 8, "reserved": 0}, 0),
    ({"on_hand": 12, "reorder_point": 6, "reserved": 2}, 0),
    ({"on_hand": 0, "reorder_point": 4, "reserved": 2}, 6),
]
need_results = []
for row, expected in need_cases:
    before = copy.deepcopy(row)
    actual = student_need(row)
    passed = actual == expected and row == before
    need_results.append(passed)
    print("PASS" if passed else "NEEDS_WORK", row, "expected", expected, "observed", actual)


def reserved_probe(quantity):
    connected = build_reserved_tools(reserved_shop, PRICES, student_need, StudentDispatcher)
    stock = connected.invoke(ToolCall(id="stock", name="list_stock", arguments={}))
    reported = next(row["needed"] for row in stock["value"] if row["sku"] == "SKU-VANILLA")
    draft = connected.invoke(
        ToolCall(
            id="draft", name="draft_order", arguments={"sku": "SKU-VANILLA", "quantity": quantity}
        )
    )
    return {
        "reported": reported,
        "ok": draft["ok"],
        "total": draft.get("value", {}).get("total_pence"),
    }


integration_expected = [
    (9, {"reported": 9, "ok": True, "total": 2250}),
    (6, {"reported": 9, "ok": False, "total": None}),
]
integration_results = []
for quantity, expected in integration_expected:
    actual = reserved_probe(quantity)
    integration_results.append(actual == expected)
    print("PASS" if actual == expected else "NEEDS_WORK", "CONNECTED", actual)```

<details><summary>Hint: derive the algebra before editing</summary>
Start with sellable stock = on hand minus reserved. Substitute that expression into
target minus sellable stock, then clamp the result at zero.
</details>

## 81–87 min · Compose the tools into a real sequence

This deterministic caller stands in for the future model's proposed sequence. Its choices are
visible, so we can test the tool boundary without a model key. **Your** need rule and dispatcher
are on the execution path. The observations come from the handlers, not a prewritten answer.

```python
connected = build_reserved_tools(reserved_shop, PRICES, student_need, StudentDispatcher)
observations = []
for request in [
    ToolCall(id="step-1", name="list_stock", arguments={}),
    ToolCall(id="step-2", name="supplier", arguments={"sku": "SKU-VANILLA"}),
    ToolCall(id="step-3", name="draft_order", arguments={"sku": "SKU-VANILLA", "quantity": 9}),
]:
    result = connected.invoke(request)
    observations.append({"call_id": request.id, "tool": request.name, "observation": result})
    print(json.dumps(observations[-1], sort_keys=True))
print("Physical stock:", reserved_shop["products"][0]["on_hand"])```

## 87–90 min · Exit ticket

Answer in your own words and point to one observed result for each:

1. Why are both the advertised schema and the execution allowlist needed?
2. Why can a refused observation fail to prove that an effect was prevented?
3. Trace `2250` backwards through your draft, price, quantity and reservation rule.
4. What did today's deterministic sequence prove? What still needs a real-model experiment?

Keep the edited notebooks and first predictions. The teacher will ask one changed case without
the visible examples. An all-green visible report is necessary evidence, not a learning-gain claim.

```python
lesson_two_report = {
    "dispatch_visible": sum(dispatch_results),
    "dispatch_total": len(dispatch_results),
    "need_visible": sum(need_results),
    "need_total": len(need_results),
    "integration_visible": sum(integration_results),
    "integration_total": len(integration_results),
    "physical_stock": reserved_shop["products"][0]["on_hand"],
    "explanations": "TEACHER_REVIEW_REQUIRED",
}
print(json.dumps(lesson_two_report, indent=2))```

## Extension bank · after the 90-minute core

Choose one; these do not replace the four core exercises.

* **New product:** add mango at one tub, target five, two reserved, price 325 pence. Predict the
  quantity and total before running the same handlers. Then remove its price
  and explain the refusal.
* **Exact empty:** build from an empty product list. Stock should be empty and an arbitrary quote
  should refuse. Add a duplicate SKU and show construction refuses instead of overwriting a row.
* **Snapshot:** build two dispatchers, change the original fixture, and show existing snapshots
  remain unchanged. Explain why this useful isolation is not a fresh-stock or concurrency guarantee.
* **Result limit:** create a local handler that appends to a list, then returns 200 characters.
  Use a 128-byte result limit. Explain the error and the retained side effect separately.
* **Your new rule:** propose a supplier pack-size constraint. Write two independently calculated
  cases before deciding how it interacts with the exact-need rule.
  Do not silently change the contract.
