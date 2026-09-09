"""Build the standalone ninety-minute Chapter 2 classroom edition."""

from __future__ import annotations

import ast
import hashlib
import json
import subprocess
import sys
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "book/always_on/classroom/ch02-90min-v1"
SOURCE = ROOT / "book/always_on/learner/ch02.py"
PIN = "4baba0a1c051d9d02af552b95a14a5b9c76f3f13"
SOURCE_TEXT = SOURCE.read_text()
TREE = ast.parse(SOURCE_TEXT)


def definition(name):
    node = next(n for n in TREE.body if getattr(n, "name", None) == name)
    source = ast.get_source_segment(SOURCE_TEXT, node)
    if node.decorator_list:
        source = (
            "\n".join(
                "@" + ast.get_source_segment(SOURCE_TEXT, item) for item in node.decorator_list
            )
            + "\n"
            + source
        )
    return source.replace(
        "except ValueError, TypeError, KeyError, PermissionError, TimeoutError, OSError:",
        "except (ValueError, TypeError, KeyError, PermissionError, TimeoutError, OSError):",
    )


def clean(value):
    return textwrap.dedent(value).strip() + "\n"


def md(value):
    return {"cell_type": "markdown", "metadata": {}, "source": clean(value)}


def code(value, tag=None):
    return {
        "cell_type": "code",
        "metadata": {"tags": [tag]} if tag else {},
        "source": clean(value),
        "execution_count": None,
        "outputs": [],
    }


SETUP = """
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
print("Python", sys.version.split()[0], "| Pydantic", pydantic.__version__)
"""

FIXTURE = """
SHOP = {
    "customer": "Lucy", "currency": "GBP",
    "products": [
        {"sku": "SKU-VANILLA", "name": "Vanilla", "on_hand": 2, "reorder_point": 8},
        {"sku": "SKU-CHOCOLATE", "name": "Chocolate", "on_hand": 12, "reorder_point": 6},
        {"sku": "SKU-STRAWBERRY", "name": "Strawberry", "on_hand": 1, "reorder_point": 5},
    ],
}
PRICES = {"SKU-VANILLA": 250, "SKU-CHOCOLATE": 300, "SKU-STRAWBERRY": 275}
products = {row["sku"]: copy.deepcopy(row) for row in SHOP["products"]}
for row in SHOP["products"]:
    print(row["sku"], "need =", max(0, row["reorder_point"] - row["on_hand"]))
"""

MODELS = "\n\n".join(definition(n) for n in ("NoArguments", "ProductArguments", "DraftArguments"))
TOOL = definition("ExecutableTool")
CALL = definition("ToolCall")
DISPATCHER = definition("Dispatcher")
FACTORY = definition("build_tools")

GRADE = '''
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
        print("PASS" if passed else "NEEDS_WORK", label,
              "| expected:", expected, "| observed:", actual)
        if supplied != before:
            print("  Input mutation detected.")
    print(f"{sum(results)}/{len(results)} visible checks passed")
    return results
'''

ARG_START = """
class StudentDraftArguments(BaseModel):
    # Exercise 1: make the complete contract strict and reject unknown fields.
    sku: str
    quantity: Any
"""
ARG_ANSWER = """
class StudentDraftArguments(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    sku: str = Field(min_length=1, max_length=100)
    quantity: int = Field(gt=0, le=1000)
"""
DRAFT_START = """
def student_draft(args, rows, prices):
    # Exercise 2: use authoritative rows and prices; return a draft or raise ValueError/KeyError.
    raise NotImplementedError("Calculate and validate the draft")
"""
DRAFT_ANSWER = """
def student_draft(args, rows, prices):
    row = rows[args.sku]
    needed = max(0, row["reorder_point"] - row["on_hand"])
    if args.quantity != needed:
        raise ValueError("quantity differs from the replenishment need")
    unit_pence = prices[args.sku]
    return {"sku": args.sku, "quantity": args.quantity,
            "unit_cost_pence": unit_pence,
            "total_pence": args.quantity * unit_pence, "status": "DRAFT"}
"""

INVOKE_START = DISPATCHER.split("    def invoke(self, call):", 1)[1]
INVOKE_START = "def student_invoke(self, call):" + textwrap.dedent(INVOKE_START).replace(
    "\n", "\n    "
)
# Keep the original implementation readable, with two deliberate ordering/permission defects.
INVOKE_START = "def student_invoke(self, call):\n" + textwrap.indent(
    textwrap.dedent(DISPATCHER.split("    def invoke(self, call):\n", 1)[1]), "    "
)
INVOKE_ANSWER = INVOKE_START
INVOKE_START = INVOKE_START.replace(
    "if tool is None or call.name not in self.allowed:",
    "if tool is None:  # BUG A: a registered tool may still be forbidden",
).replace(
    "        if tool.consequential:\n            self.before_write(call)\n"
    "        value = tool.handler(arguments)",
    "        value = tool.handler(arguments)  # BUG B: inspect the execution order\n"
    "        if tool.consequential:\n            self.before_write(call)",
)

NEED_START = """
def student_need(row):
    # Exercise 4: account for units already reserved for catering.
    return max(0, row["reorder_point"] - row["on_hand"])
"""
NEED_ANSWER = """
def student_need(row):
    return max(0, row["reorder_point"] - row["on_hand"] + row.get("reserved", 0))
"""


def opening(number, title, minutes):
    return [
        md(f"""# Chapter 2 · {number}. {title}

**{minutes} minutes · Student classroom edition · 9 September 2026**

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
"""),
        code(SETUP, "setup"),
    ]


def notebook_one(instructor=False):
    c = opening(1, "From a model request to a trustworthy draft", 45)
    c[1]["source"] = c[1]["source"].replace("from types import MappingProxyType\n", "")
    c += [
        md("""## 0–5 min · The problem is a boundary

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
"""),
        code(FIXTURE, "worked-example"),
        md("""## 5–10 min · Why ordinary Python types need an explicit boundary

Python permits useful operations that would be wrong for this business contract.
Predict the two expressions, then inspect the actual value and type. Does `isinstance` express
the exact integer contract we need?
"""),
        code("""print("string multiplication:", repr("6" * 3))
print("boolean arithmetic:", True * 250)
print("isinstance(True, int):", isinstance(True, int))
quantity = True
print("type(quantity) is int:", type(quantity) is int)

class ConvenientArguments(BaseModel):
    quantity: int

print("coerced string:", ConvenientArguments.model_validate({"quantity": "6"}).quantity)
"""),
        md("""
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
"""),
        code(ARG_ANSWER if instructor else ARG_START, "exercise-1"),
        code(
            """argument_cases = [
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
print("Exercise 1:", sum(schema_results), "/", len(schema_results))
""",
            "feedback",
        ),
        md("""<details><summary>Hint 1: where strictness belongs</summary>
Put the configuration on the model class so every field uses the same input policy.
</details>
<details><summary>Hint 2: field bounds</summary>
`min_length`/`max_length` constrain text; `gt`/`le` constrain integer values.
A type annotation alone does not impose these bounds.
</details>

**Pair check:** should a perfectly formatted but unknown SKU pass this schema? Explain why.
The next examples use the book's reference models explicitly, so an unfinished Exercise 1 does
not prevent exploring the business layer. Your Exercise 1 result remains separate.
"""),
        code(MODELS, "book-reference"),
        code("""
valid_but_wrong = DraftArguments.model_validate({"sku": "SKU-VANILLA", "quantity": 7})
print("Schema accepted:", valid_but_wrong.model_dump())
print("Actual shop need:", max(0, products[valid_but_wrong.sku]["reorder_point"]
                              - products[valid_but_wrong.sku]["on_hand"]))
"""),
        md("""## 18–30 min · Exercise 2: make the business rule executable

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
"""),
        code(DRAFT_ANSWER if instructor else DRAFT_START, "exercise-2"),
        code(GRADE),
        code(
            """def draft_case(payload, rows, prices):
    args = DraftArguments.model_validate(payload)
    return student_draft(args, rows, prices)

draft_cases = [
    ("vanilla six", [{"sku": "SKU-VANILLA", "quantity": 6}, products, PRICES],
     {"sku": "SKU-VANILLA", "quantity": 6, "unit_cost_pence": 250,
      "total_pence": 1500, "status": "DRAFT"}),
    ("over-order seven", [{"sku": "SKU-VANILLA", "quantity": 7}, products, PRICES],
     {"raised": "ValueError"}),
    ("strawberry four", [{"sku": "SKU-STRAWBERRY", "quantity": 4}, products, PRICES],
     {"sku": "SKU-STRAWBERRY", "quantity": 4, "unit_cost_pence": 275,
      "total_pence": 1100, "status": "DRAFT"}),
    ("missing SKU", [{"sku": "SKU-MISSING", "quantity": 1}, products, PRICES],
     {"raised": "KeyError"}),
    ("missing price", [{"sku": "SKU-VANILLA", "quantity": 6}, products, {}],
     {"raised": "KeyError"}),
]
draft_results = check_cases(draft_case, draft_cases)
""",
            "feedback",
        ),
        md("""<details><summary>Hint 1: do not trust the requested quantity</summary>
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
"""),
        code(TOOL, "book-reference"),
        code("""student_tool = ExecutableTool(
    "draft_order", "Calculate a draft using authoritative shop records; never purchases.",
    DraftArguments, lambda args: student_draft(args, products, PRICES),
)
schema = student_tool.schema()
print(json.dumps(schema, indent=2))
print("Model-visible argument names:", sorted(schema["function"]["parameters"]["properties"]))
"""),
        md("""Find `additionalProperties`, the integer bounds, and `required` in the printed schema.
There is no `unit_cost_pence` input. Now trace the request through the schema and into your handler.
If Exercise 2 is unfinished, the connection should remain unfinished too.
"""),
        code(
            """payload = {"sku": "SKU-VANILLA", "quantity": 6}
typed = student_tool.arguments.model_validate(payload, strict=True)
try:
    connected_draft = student_tool.handler(typed)
    print("YOUR CONNECTED TOOL:", connected_draft)
except NotImplementedError:
    connected_draft = None
    print("NEEDS_WORK: complete Exercise 2, then rerun this connection.")
print("Physical stock remains:", products["SKU-VANILLA"]["on_hand"])
""",
            "integration",
        ),
        md("""## 38–43 min · Transfer: change the data, keep the mechanism

Mango has one tub, target five, and price 325 pence. Predict the correct quantity and total before
running. Then change only its price to 350. The same handler should produce a different total.
This tests whether your code computes a result or recognizes an example.
"""),
        code(
            """mango_rows = {"SKU-MANGO": {"sku": "SKU-MANGO", "on_hand": 1, "reorder_point": 5}}
transfer_cases = [
    ("mango 325p", [{"sku": "SKU-MANGO", "quantity": 4}, mango_rows, {"SKU-MANGO": 325}],
     {"sku": "SKU-MANGO", "quantity": 4, "unit_cost_pence": 325,
      "total_pence": 1300, "status": "DRAFT"}),
    ("mango 350p", [{"sku": "SKU-MANGO", "quantity": 4}, mango_rows, {"SKU-MANGO": 350}],
     {"sku": "SKU-MANGO", "quantity": 4, "unit_cost_pence": 350,
      "total_pence": 1400, "status": "DRAFT"}),
    ("under-order", [{"sku": "SKU-MANGO", "quantity": 3}, mango_rows, {"SKU-MANGO": 350}],
     {"raised": "ValueError"}),
]
transfer_results = check_cases(draft_case, transfer_cases)
""",
            "transfer",
        ),
        md("""## 43–45 min · Retrieval checkpoint

Without looking back, explain:

1. Why can `7` pass the schema and still fail the operation?
2. Where do the unit price and total come from?
3. What is the difference between describing a tool and invoking it?
4. Which observed state proves this example did not change inventory?

Save your edited notebook. Open Notebook 2 next; it has its own setup and does not require
copying a handoff file. The repository's longer successor units remain follow-on practice.
"""),
        code(
            """lesson_one_report = {
    "schema_visible": sum(schema_results), "schema_total": len(schema_results),
    "draft_visible": sum(draft_results), "draft_total": len(draft_results),
    "transfer_visible": sum(transfer_results), "transfer_total": len(transfer_results),
    "connected": connected_draft is not None,
    "explanations": "TEACHER_REVIEW_REQUIRED",
}
print(json.dumps(lesson_one_report, indent=2))
""",
            "report",
        ),
    ]
    return c


EXTENSION_FACTORY = '''
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
        return {"sku": args.sku, "supplier": "lucy-local", "currency": "GBP",
                "unit_cost_pence": saved_prices[args.sku]}

    def draft(args):
        if args.quantity != need(rows[args.sku]):
            raise ValueError("quantity differs from current need")
        price = quote(ProductArguments(sku=args.sku))
        return {**price, "quantity": args.quantity,
                "total_pence": args.quantity * price["unit_cost_pence"], "status": "DRAFT"}

    tools = [ExecutableTool("list_stock", "Read stock and need.", NoArguments, stock),
             ExecutableTool("supplier", "Read price.", ProductArguments, quote),
             ExecutableTool("draft_order", "Calculate a draft.", DraftArguments, draft)]
    return dispatcher_type(tools, allowed=frozenset(tool.name for tool in tools))
'''


def notebook_two(instructor=False):
    c = opening(2, "Build the execution boundary and challenge it", 45)
    c += [
        md("""## 45–50 min · Reassemble the path

This notebook is independently runnable. The supplied models and tool class are reference code
from the book, not credit for Exercise 1. Your work here is repairing dispatch and extending the
stock rule through the connected system.

The dispatcher decides **whether a request may reach its handler**. Trace this path:

`tool name → registry + allowlist → strict arguments → authority check → handler → JSON result`

Which check should reject an unknown name? Which must happen before an effect? Can a schema
advertised to a model enforce permission by itself?
"""),
        code(FIXTURE),
        code(MODELS + "\n\n" + TOOL + "\n\n" + CALL, "book-reference"),
        md("""### Read the actual dispatcher, one boundary at a time

Annotate the code below with the five checks in the path. `MappingProxyType` prevents ordinary
registry assignment; a `frozenset` describes the caller's allowed operations. Neither is a
substitute for checking every invocation.

The final byte limit is checked **after** the handler returns. It limits the returned observation,
not the handler's execution time, memory, or effects. This is trusted local code, not a sandbox.
"""),
        code(DISPATCHER, "book-reference"),
        code(FACTORY, "book-reference"),
        code("""reference_shop = build_tools(SHOP)
good_call = ToolCall(id="demo", name="draft_order",
                     arguments={"sku": "SKU-VANILLA", "quantity": 6})
print(reference_shop.invoke(good_call))
assert reference_shop.invoke(good_call)["value"]["total_pence"] == 1500
"""),
        md("""## 50–55 min · Distinguish the refusal layers

Before execution, label each request: **name/permission**, **argument schema**,
or **business rule**.
The last two business failures share `tool_failed` externally. A short public error code need
not expose raw input or an arbitrary internal exception message.
"""),
        code("""requests = [
    ToolCall(id="name", name="run_shell", arguments={}),
    ToolCall(id="type", name="draft_order", arguments={"sku": "SKU-VANILLA", "quantity": True}),
    ToolCall(id="extra", name="draft_order",
             arguments={"sku": "SKU-VANILLA", "quantity": 6, "approved": True}),
    ToolCall(id="need", name="draft_order", arguments={"sku": "SKU-VANILLA", "quantity": 7}),
    ToolCall(id="sku", name="supplier", arguments={"sku": "UNKNOWN"}),
]
for call in requests:
    print(call.id, reference_shop.invoke(call))
"""),
        md("""## 55–68 min · Exercise 3: repair two independent dispatcher defects

The following is a working copy of the chapter's `invoke`, with **two deliberate bugs**.
Repair this cell, then rerun the instrumentation below.

* A tool may be registered but forbidden to this caller. Repair the execution check.
* A refusing authority callback must prevent the handler from running. Repair the order.

Do not change the tests or replace every result with a refusal. A legitimate allowed call must
still execute exactly once. First predict the error response
**and the handler count** for each case.
"""),
        code(INVOKE_ANSWER if instructor else INVOKE_START, "exercise-3"),
        code(
            """class StudentDispatcher(Dispatcher):
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
    tool = ExecutableTool("probe", "Harmless local instrumentation.", NoArguments,
                          handler, consequential=consequential)
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
print("Exercise 3:", sum(dispatch_results), "/", len(dispatch_results))
""",
            "feedback",
        ),
        md("""<details><summary>Hint 1: registry versus permission</summary>
Existence in `self.tools` answers whether the implementation is known. Membership in `self.allowed`
answers whether this caller may invoke it. Both are required.
</details>
<details><summary>Hint 2: an error result can arrive too late</summary>
Find the first line that can call the handler. Any authority callback
that can refuse must run before it.
</details>

**Explain the observation:** in the broken version, the refused call returns an error even though
the handler ran. Why would grading only `response["ok"]` miss the bug?

## 68–72 min · The stock report and the draft can disagree

Lucy now reserves three vanilla tubs for a catering order. Sellable stock is `on_hand - reserved`.
The replenishment rule becomes `max(0, target - on_hand + reserved)`.
For two on hand, target eight and three reserved, the need is **nine**.

Run the old book factory on this new fixture. It still reports six because reservations were
not part of its original contract. Merely adding a data field does not implement new behavior.
"""),
        code("""reserved_shop = copy.deepcopy(SHOP)
reserved_shop["products"][0]["reserved"] = 3
old = build_tools(reserved_shop)
old_stock = old.invoke(ToolCall(id="old-stock", name="list_stock", arguments={}))
print("Original rule:", next(row["needed"] for row in old_stock["value"]
                             if row["sku"] == "SKU-VANILLA"))
print("Nine-tub draft:", old.invoke(ToolCall(id="new-need", name="draft_order",
      arguments={"sku": "SKU-VANILLA", "quantity": 9})))
"""),
        md("""## 72–82 min · Exercise 4: one invariant, two call sites

The teaching extension below passes one `need` function to both stock reporting and draft
validation. Follow both uses. This is an explicit extension of the chapter's factory; the
dispatcher and typed contracts remain the actual book definitions.

Implement `student_need`. Inputs are trusted rows with nonnegative integer stock, target and
reservation counts; absent `reserved` means zero. Do not change stock or reserve additional units.
Check an exact-zero result, a surplus, and a reservation greater than current physical stock.
"""),
        code(NEED_ANSWER if instructor else NEED_START, "exercise-4"),
        code(EXTENSION_FACTORY, "integration"),
        code(
            """need_cases = [
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
    draft = connected.invoke(ToolCall(id="draft", name="draft_order",
                             arguments={"sku": "SKU-VANILLA", "quantity": quantity}))
    return {"reported": reported, "ok": draft["ok"],
            "total": draft.get("value", {}).get("total_pence")}

integration_expected = [
    (9, {"reported": 9, "ok": True, "total": 2250}),
    (6, {"reported": 9, "ok": False, "total": None}),
]
integration_results = []
for quantity, expected in integration_expected:
    actual = reserved_probe(quantity)
    integration_results.append(actual == expected)
    print("PASS" if actual == expected else "NEEDS_WORK", "CONNECTED", actual)
""",
            "feedback",
        ),
        md("""<details><summary>Hint: derive the algebra before editing</summary>
Start with sellable stock = on hand minus reserved. Substitute that expression into
target minus sellable stock, then clamp the result at zero.
</details>

## 82–87 min · Compose the tools into a real sequence

This deterministic caller stands in for the future model's proposed sequence. Its choices are
visible, so we can test the tool boundary without a model key. **Your** need rule and dispatcher
are on the execution path. The observations come from the handlers, not a prewritten answer.
"""),
        code(
            """
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
print("Physical stock:", reserved_shop["products"][0]["on_hand"])
""",
            "capstone",
        ),
        md("""## 87–90 min · Exit ticket

Answer in your own words and point to one observed result for each:

1. Why are both the advertised schema and the execution allowlist needed?
2. Why can a refused observation fail to prove that an effect was prevented?
3. Trace `2250` backwards through your draft, price, quantity and reservation rule.
4. What did today's deterministic sequence prove? What still needs a real-model experiment?

Keep the edited notebooks and first predictions. The teacher will ask one changed case without
the visible examples. An all-green visible report is necessary evidence, not a learning-gain claim.
"""),
        code(
            """lesson_two_report = {
    "dispatch_visible": sum(dispatch_results), "dispatch_total": len(dispatch_results),
    "need_visible": sum(need_results), "need_total": len(need_results),
    "integration_visible": sum(integration_results), "integration_total": len(integration_results),
    "physical_stock": reserved_shop["products"][0]["on_hand"],
    "explanations": "TEACHER_REVIEW_REQUIRED",
}
print(json.dumps(lesson_two_report, indent=2))
""",
            "report",
        ),
        md("""## Extension bank · after the 90-minute core

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
"""),
    ]
    return c


def write_notebook(path, cells, instructor):
    if instructor:
        cells.insert(
            0,
            md(
                "# INSTRUCTOR ANSWERS — do not distribute as the student notebook\n"
                "This copy replaces the four exercise starters with worked answers. "
                "Retain student attempts before showing it. The final instructor checks "
                "include additional inputs not in the student feedback tables."
            ),
        )
    for index, cell in enumerate(cells):
        cell["id"] = hashlib.sha256(f"{path.name}:{index}".encode()).hexdigest()[:12]
    notebook = {
        "cells": cells,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "version": "3.10"},
            "chapter_source": {
                "commit": PIN,
                "path": str(SOURCE.relative_to(ROOT)),
                "sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
            },
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(notebook, indent=1, ensure_ascii=False) + "\n")
    subprocess.run([sys.executable, "-m", "ruff", "check", "--fix", str(path)], check=True)
    subprocess.run([sys.executable, "-m", "ruff", "format", str(path)], check=True)
    cells = json.loads(path.read_text())["cells"]
    markdown = []
    for cell in cells:
        if isinstance(cell["source"], list):
            cell["source"] = "".join(cell["source"])
        if cell["cell_type"] == "markdown":
            markdown.append(cell["source"])
        else:
            markdown.append("```python\n" + cell["source"] + "```\n")
    path.with_suffix(".md").write_text("\n".join(markdown))


def main():
    saved = subprocess.check_output(
        ["git", "show", f"{PIN}:book/always_on/learner/ch02.py"], cwd=ROOT
    )
    assert saved == SOURCE.read_bytes(), "The pinned classroom source changed"
    for instructor in (False, True):
        folder = OUT / ("instructor" if instructor else "student")
        one, two = notebook_one(instructor), notebook_two(instructor)
        if instructor:
            one += [
                md(
                    "## Instructor-only transfer checks\n"
                    "Do not reveal these before the learner attempt."
                ),
                code(
                    """
assert all(schema_results) and all(draft_results) and all(transfer_results)
assert connected_draft["total_pence"] == 1500
assert products["SKU-VANILLA"]["on_hand"] == 2
pear = {"SKU-PEAR": {"sku": "SKU-PEAR", "on_hand": 2, "reorder_point": 9}}
assert student_draft(DraftArguments(sku="SKU-PEAR", quantity=7), pear,
                     {"SKU-PEAR": 175})["total_pence"] == 1225
print("INSTRUCTOR CHECKS: notebook 1 passed")
""",
                    "instructor-check",
                ),
            ]
            two += [
                md(
                    "## Instructor-only transfer checks\n"
                    "Require both successful execution and actual prevention."
                ),
                code(
                    """
assert all(dispatch_results) and all(need_results) and all(integration_results)
assert student_need({"on_hand": 4, "reorder_point": 9, "reserved": 2}) == 7
empty = build_reserved_tools({"products": []}, {}, student_need, StudentDispatcher)
assert empty.invoke(ToolCall(id="empty", name="list_stock", arguments={}))["value"] == []
assert empty.invoke(ToolCall(id="absent", name="supplier", arguments={"sku": "X"}))["ok"] is False
try:
    build_reserved_tools({"products": [SHOP["products"][0], SHOP["products"][0]]},
                         PRICES, student_need, StudentDispatcher)
except ValueError:
    pass
else:
    raise AssertionError("Duplicate identities were accepted")
events = []
tool = ExecutableTool("oversize", "Local effect experiment.", NoArguments,
                      lambda _: (events.append("ran") or "x" * 200))
bounded = StudentDispatcher([tool], allowed=frozenset({"oversize"}), max_result_bytes=128)
assert bounded.invoke(ToolCall(id="large", name="oversize", arguments={})) == {
    "ok": False, "error": "result_too_large"}
assert events == ["ran"]
assert observations[-1]["observation"]["value"]["total_pence"] == 2250
print("INSTRUCTOR CHECKS: notebook 2 passed")
""",
                    "instructor-check",
                ),
            ]
        write_notebook(folder / "01-typed-tools-and-trustworthy-drafts-v1.ipynb", one, instructor)
        write_notebook(folder / "02-dispatch-permissions-and-transfer-v1.ipynb", two, instructor)
    print("Built four classroom notebooks and Markdown companions at", OUT)


if __name__ == "__main__":
    main()
