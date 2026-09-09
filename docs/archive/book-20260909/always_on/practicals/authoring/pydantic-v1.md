### Pydantic: turn an input dictionary into a checked object

Pydantic is an additional Python library for validating data. Its **model** is a class describing
fields, not a neural network. Inherit from `BaseModel`, declare annotated fields, then call
`model_validate` on incoming data. A field without a default is required. A field with a default
can be omitted. The result is an instance whose values you read with dot notation.

```python tags=["foundation", "worked-example"]
from pydantic import BaseModel, ConfigDict, Field, ValidationError


class IntroCourseRequest(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")
    name: str = Field(min_length=1)
    quantity: int = Field(gt=0, le=1000)
    note: str = ""


intro_request = IntroCourseRequest.model_validate({"name": "mango", "quantity": 4})
print(intro_request.name, intro_request.quantity, repr(intro_request.note))
assert intro_request.note == ""
```

The annotation says the field's type. `Field` supplies constraints: `gt=0` means greater than
zero, `le=1000` means at most 1000, and `min_length=1` excludes an empty name. `ConfigDict` sets
model-wide behavior. `strict=True` rejects conversions for this integer field, including `"4"`,
`4.0` and `True`; `extra="forbid"` rejects undeclared keys. Pydantic can otherwise convert some
compatible inputs, so choose this boundary deliberately rather than assuming every accepted
input arrived in the expected type.

Predict which rule refuses each payload. `ValidationError` reports a failed contract. Its
`errors()` entries contain `loc`, the field location, and `type`, the failure category. Catching
that expected exception lets the notebook inspect the failure and continue.

```python tags=["foundation", "worked-example"]
intro_bad_requests = [
    {"name": "mango", "quantity": "4"},
    {"name": "mango", "quantity": True},
    {"name": "", "quantity": 4},
    {"name": "mango", "quantity": 0},
    {"name": "mango", "quantity": 4, "approved": True},
    {"quantity": 4},
]
for intro_bad_request in intro_bad_requests:
    try:
        IntroCourseRequest.model_validate(intro_bad_request)
    except ValidationError as intro_error:
        print([(item["loc"], item["type"]) for item in intro_error.errors(include_input=False)])
    else:
        raise AssertionError("An invalid input crossed the declared contract")
```

Use `model_dump()` for a Python dictionary, `model_dump_json()` for JSON text, and
`model_validate_json()` to parse and validate JSON. `model_json_schema()` describes the contract;
it is neither an instance's current values nor an invocation of the business handler.

```python tags=["foundation", "worked-example"]
intro_serialized = intro_request.model_dump_json()
intro_schema = IntroCourseRequest.model_json_schema()
assert IntroCourseRequest.model_validate_json(intro_serialized) == intro_request
print("Actual values:", intro_request.model_dump())
print("Quantity contract:", intro_schema["properties"]["quantity"])
assert intro_schema["properties"]["quantity"]["exclusiveMinimum"] == 0
```

Four is valid input to this schema even if the shop needs six. Pydantic checks the declared
shape and constraints; the handler still needs authoritative stock, price and permission.
Ordinary assignments to an existing instance are not automatically revalidated unless configured
for assignment validation. This lesson validates new input at the boundary and uses the resulting
values. Explain these limits before relying on a model object in a transaction or tool call.

Chapter 2's full introduction expands this pattern with a separate data-repair checkpoint.
This notebook contains the required pattern here so prior Pydantic experience is not needed.
References: [models](https://docs.pydantic.dev/latest/concepts/models/),
[fields](https://docs.pydantic.dev/latest/concepts/fields/), and
[strict mode](https://docs.pydantic.dev/latest/concepts/strict_mode/).
