"""Add a self-contained Pydantic lesson without rewriting the published v1 pack."""

from __future__ import annotations

import json
import runpy
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PREVIOUS = ROOT / "book/always_on/classroom/ch02-90min-v1"
OUT = ROOT / "book/always_on/classroom/ch02-90min-v2"
BASE = runpy.run_path(str(ROOT / "scripts/build_ch02_classroom_v1.py"))
md, code = BASE["md"], BASE["code"]


def primer(instructor):
    return [
        md("""## Pydantic from first principles · 20-minute guided introduction

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
"""),
        code(
            """
def annotated_double(quantity: int) -> int:
    return quantity * 2

incoming_quantity = "6"
observed = annotated_double(incoming_quantity)
print(repr(observed), type(observed).__name__)
assert observed == "66"
""",
            "pydantic-worked-example",
        ),
        md("""The result is `'66'`, a string. The annotation did not become a runtime guard.
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
"""),
        code(
            """
class IntroLine(BaseModel):
    sku: str
    quantity: int
    note: str = ""

line = IntroLine(sku="SKU-VANILLA", quantity=6)
incoming = {"sku": "SKU-VANILLA", "quantity": 6}
parsed_line = IntroLine.model_validate(incoming)
print(line.sku, line.quantity, repr(line.note))
print("Same values:", line == parsed_line)
assert line.note == "" and line == parsed_line
""",
            "pydantic-worked-example",
        ),
        md("""### 3. Read an error as a repair instruction · minutes 5–7

Now omit `sku` and supply a quantity that cannot be parsed as an integer. Pydantic raises
`ValidationError` instead of returning a usable instance. Catch this expected exception so
the notebook can show the failure and continue. Its `errors()` method returns structured
details: `loc` identifies the field, `type` classifies the failure, and `msg` explains it.
We hide the raw input in this display; we need the location and rule to understand the failure.

**Predict:** how many fields need repair? A missing required field is different from a field
with an invalid value. Read every reported error, not just the first line.
"""),
        code(
            """
bad_line = {"quantity": "six"}
try:
    IntroLine.model_validate(bad_line)
except ValidationError as error:
    details = error.errors(include_url=False, include_input=False)
    for detail in details:
        print(detail["loc"], detail["type"], detail["msg"])
    assert {item["loc"] for item in details} == {("sku",), ("quantity",)}
else:
    raise AssertionError("The invalid line was accepted")
""",
            "pydantic-worked-example",
        ),
        md("""Both fields need attention. An exception is useful feedback here, not a notebook setup
failure. In the tool dispatcher later, this same exception becomes a refused observation.
Validation reports the problem; it does not decide whether to ask the caller to correct it.

### 4. Accepted input can be converted input · minutes 7–10

By default, Pydantic may convert compatible input into the declared type. That is helpful for
a form but can hide what a tool caller actually sent. For an integer field, compare `6`,
`"6"`, `True`, `6.0`, and `"six"`. **Write the two acceptance columns before running.**
The `strict=True` argument asks this validation call to reject these integer conversions.
This table concerns Python inputs to an integer field; strict handling of JSON dates and other
types has additional rules. We do not generalize this table to every type.
"""),
        code(
            """
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
    print(repr(value), "| default:", inspect_quantity(value, False),
          "| strict:", inspect_quantity(value, True))
assert [inspect_quantity(value, True) != "REFUSED" for value in quantity_inputs] == [
    True, False, False, False, False,
]
boolean_quantity = True
print("Python considers bool an int subclass:", isinstance(boolean_quantity, int))
print("Its exact type is int:", type(boolean_quantity) is int)
""",
            "pydantic-worked-example",
        ),
        md("""Default validation converts the first four values to integers. The strict
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
"""),
        code(
            """
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
    assert accepted == expected
""",
            "pydantic-worked-example",
        ),
        md("""### 6. Dictionary, instance, JSON, schema · minutes 13–16

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
"""),
        code(
            """
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
assert schema_description["additionalProperties"] is False
""",
            "pydantic-worked-example",
        ),
        md("""### 7. Validation is a contract check, not a fact check · minutes 16–17

An invented count of 999 satisfies our type and range rules. Pydantic has no connection to
Lucy's shelf and cannot know whether that count is true. We must compare it with an
authoritative source separately. Similarly, validating an `approved` field in some other
schema would not establish that a real person authorized a purchase.

The model also does not promise that ordinary assignments to an existing instance are
revalidated: assignment validation is a separate configuration option. In this lesson we
validate new input at the boundary and then use its fields; we do not use unvalidated updates.
"""),
        code(
            """
plausible_but_unverified = IntroStockReading(sku="SKU-VANILLA", on_hand=999)
authoritative_count = 2
print("Passes the declared contract:", plausible_but_unverified.on_hand)
print("Matches the shop record:", plausible_but_unverified.on_hand == authoritative_count)
assert plausible_but_unverified.on_hand != authoritative_count
""",
            "pydantic-worked-example",
        ),
        md("""### 8. Your turn: repair the data without weakening the contract · minutes 17–20

The authoritative record says SKU `SKU-VANILLA` has **2** tubs. Repair `repaired_stock`
in the next cell so it represents that record and passes `IntroStockReading`. Keep the model
unchanged. Before running, name all three problems with the supplied dictionary. Explain
why changing a type annotation to `Any` would hide a problem rather than repair this data.

Hint 1: inspect the required names and each value's Python type.
Hint 2: an empty string is still a string, but the length constraint matters.
Hint 3: the data contract has exactly two fields. A proposed approval is not stock data.
"""),
        code(
            'repaired_stock = {"sku": "SKU-VANILLA", "on_hand": 2}\n'
            if instructor
            else 'repaired_stock = {"sku": "", "on_hand": "2", "approved": True}\n',
            "pydantic-checkpoint",
        ),
        code(
            """
try:
    repaired_reading = IntroStockReading.model_validate(repaired_stock)
except ValidationError as error:
    pydantic_checkpoint = False
    for detail in error.errors(include_url=False, include_input=False):
        print(detail["loc"], detail["msg"])
else:
    pydantic_checkpoint = repaired_reading.model_dump() == {
        "sku": "SKU-VANILLA", "on_hand": 2,
    }
print("PASS" if pydantic_checkpoint else "NEEDS_WORK", "Pydantic data-repair checkpoint")
""",
            "pydantic-feedback",
        ),
        md("""### Retrieve the mechanism before continuing

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
"""),
    ]


def main():
    saved = subprocess.check_output(
        ["git", "show", f"{BASE['PIN']}:book/always_on/learner/ch02.py"], cwd=ROOT
    )
    assert saved == BASE["SOURCE"].read_bytes(), "The pinned classroom source changed"
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / ".ruff.toml").write_text((PREVIOUS / ".ruff.toml").read_text())
    timings = {
        "0–5 min": "0–2 min",
        "10–18 min": "22–28 min",
        "18–30 min": "28–40 min",
        "30–38 min": "40–46 min",
        "38–43 min": "46–48 min",
        "43–45 min": "48–50 min",
        "45–50 min": "50–54 min",
        "50–55 min": "54–57 min",
        "55–68 min": "57–68 min",
        "68–72 min": "68–71 min",
        "72–82 min": "71–81 min",
        "82–87 min": "81–87 min",
    }
    for instructor in (False, True):
        for number in (1, 2):
            cells = BASE["notebook_one" if number == 1 else "notebook_two"](instructor)
            for cell in cells:
                if cell["cell_type"] == "markdown":
                    source = cell["source"]
                    for before, after in timings.items():
                        source = source.replace(before, after)
                    source = source.replace(
                        "**45 minutes", f"**{50 if number == 1 else 40} minutes"
                    )
                    source = source.replace(
                        "The only additional package is Pydantic 2.",
                        "The only additional package is Pydantic 2. "
                        "No Pydantic experience is assumed; "
                        "the introduction below teaches it from the beginning.",
                    )
                    cell["source"] = source
            if number == 1:
                assert "Why ordinary Python types" in cells[4]["source"]
                cells[4:6] = primer(instructor)
            else:
                cells[2:2] = [
                    md("""## Choose your starting point

**Continuing notebook 1:** retrieve the five primer questions, then jump to
**50–54 min · Reassemble**. The introduction below repeats the same lesson
so this notebook can stand alone. Run All can safely execute its examples.

**Starting here:** work through the 20-minute introduction first, then the
40-minute dispatcher lesson. Clock labels after the primer refer to the full class;
your standalone session takes about 60 minutes before extensions.
"""),
                    *primer(instructor),
                ]
            folder = "instructor" if instructor else "student"
            previous = next((PREVIOUS / folder).glob(f"0{number}-*.ipynb"))
            if instructor:
                previous_cells = json.loads(previous.read_text())["cells"]
                checks = [
                    c for c in previous_cells if "instructor-check" in c["metadata"].get("tags", [])
                ]
                assert len(checks) == 1
                source = checks[0]["source"]
                if isinstance(source, list):
                    source = "".join(source)
                cells += [
                    md("## Instructor-only transfer checks"),
                    code("assert pydantic_checkpoint\n" + source, "instructor-check"),
                ]
            BASE["write_notebook"](
                OUT / folder / previous.name.replace("-v1", "-v2"), cells, instructor
            )
    print("Built Pydantic-first classroom v2:", OUT)


if __name__ == "__main__":
    main()
