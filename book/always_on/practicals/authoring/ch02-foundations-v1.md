## From a Python function to a shop tool

A **tool** is a program operation exposed through a named interface. In this chapter the stock
tool reads a copied shop snapshot, the supplier tool reads a price, and the draft tool calculates
an order proposal. The interface has a name, an argument contract and a handler. The **handler**
is the Python function that actually performs the operation. Advertising a schema describes
possible arguments; invoking a handler causes behavior.

Pydantic is introduced in full below. As you work through it, keep three independent questions
in view: is the argument well formed, does it agree with the current business rule, and is this
caller permitted to execute the operation? A positive integer can pass the first question and
fail the second. A valid request can pass both and still be outside the caller's allowlist.

### Calculate before designing an interface

Work with integer pence so multiplication does not introduce a floating-point rounding question.
The SKU is a stable product identifier; the display name may change without changing identity.
An empty catalog means no products. Two rows with the same SKU are ambiguous and must not
silently overwrite each other during construction.

```python tags=["foundation", "worked-example"]
intro_shop = [
    {"sku": "MANGO", "on_hand": 1, "target": 5, "price_pence": 325},
    {"sku": "COCOA", "on_hand": 9, "target": 6, "price_pence": 300},
]
for intro_product in intro_shop:
    intro_needed = max(0, intro_product["target"] - intro_product["on_hand"])
    intro_total = intro_needed * intro_product["price_pence"]
    print(intro_product["sku"], intro_needed, intro_total)
assert 4 * 325 == 1300
```

Mango needs four tubs, costing 1300 pence. Cocoa needs none. A draft requesting three mango tubs
is type-correct but inconsistent with our exact-need contract. The handler must obtain the
authoritative price itself; accepting a caller's invented total would move the calculation's
authority to untrusted input.

### Observe why a snapshot is copied

A closure can retain access to a shop dictionary. Without a deep copy, another part of the
program can mutate that dictionary after the tools are built and silently change what an
existing tool sees. A copied snapshot makes this particular experiment repeatable. It does
not promise that a real shop never changes; refreshing stale stock is a separate contract.

```python tags=["foundation", "worked-example"]
import copy

intro_original = {"MANGO": {"on_hand": 1, "target": 5}}
intro_snapshot = copy.deepcopy(intro_original)


def intro_stock_handler():
    return copy.deepcopy(intro_snapshot)


intro_original["MANGO"]["on_hand"] = 20
intro_observed_stock = intro_stock_handler()
assert intro_observed_stock["MANGO"]["on_hand"] == 1
intro_observed_stock["MANGO"]["on_hand"] = 99
assert intro_stock_handler()["MANGO"]["on_hand"] == 1
print("Neither external input mutation nor output mutation changed the retained snapshot.")
```

The two copies protect different directions: the first prevents mutation through the original
input; the second prevents mutation through a returned result. Explain both before writing
the factory. A factory is simply a function that constructs and returns configured objects.

### Trace the three boundaries

`ToolCall` holds the requested name and arguments. `ExecutableTool` associates a name with
a Pydantic parameter class and a handler. `Dispatcher.invoke` looks up the name, checks the
allowlist, validates arguments and invokes the handler. The order matters: a refusal returned
after the handler runs cannot undo a side effect. For consequential operations, the authority
callback belongs before the handler. Our draft-only shop tools do not send purchases.

The construction exercise asks for the complete factory, not three constant answers. It must
work with a changed shop, empty input and duplicate identities. The transfer adds reservations:
sellable stock becomes physical stock minus reserved stock. Both reporting and draft validation
must use the same revised rule, or the interface can contradict itself.
