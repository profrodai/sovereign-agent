### Reading the Python vocabulary used in this notebook

You need basic assignments, `if`, loops, functions, lists and dictionaries. The less familiar
features used by the supplied code are introduced here. A **library** is reusable code that
Python can import. The **standard library** ships with Python; Pydantic is an additional package.
An import makes a name available, but does not mean that you have completed the exercise.

**JSON** is text for exchanging structured values. A Python dictionary is an in-memory object;
the JSON representation is a string. Use `json.dumps` to encode and `json.loads` to decode.
Decoding proves that text has valid JSON syntax, not that its fields match our business contract.
Predict which of the following two decoded objects could describe a stock count.

```python tags=["foundation", "worked-example"]
import json

intro_data = {"sku": "MANGO", "count": 3}
intro_text = json.dumps(intro_data, sort_keys=True)
print(type(intro_data).__name__, type(intro_text).__name__, intro_text)
print(json.loads(intro_text))
print("Also valid JSON:", json.loads('["not", "a", "stock", "record"]'))
assert json.loads(intro_text) == intro_data
```

The first result is a dictionary; the second is a list. Before indexing a decoded object,
check the shape that your function promises to accept. An **exception** interrupts the normal
path. `raise ValueError(...)` refuses an invalid value; `try`/`except` lets a caller inspect that
expected refusal. Catch the expected class, rather than turning every programming error into
apparent success. `finally` runs cleanup even when an earlier operation raises.

An **annotation**, such as `count: int`, documents the expected type. It does not by itself
enforce the type at runtime. A **class** defines a kind of object; an instance holds one object's
data. `@dataclass` asks Python to generate routine construction and comparison methods from
annotated fields. `frozen=True` prevents ordinary reassignment of the instance's fields; it does
not make every object nested inside those fields immutable. A **method** is a function attached
to a class; `self` refers to the instance receiving the call.

```python tags=["foundation", "worked-example"]
from dataclasses import dataclass


@dataclass(frozen=True)
class IntroObservation:
    operation: str
    count: int


intro_observation = IntroObservation("count-mango", 3)
print(intro_observation.operation, intro_observation.count)
assert intro_observation == IntroObservation("count-mango", 3)
```

A **callback** is a function passed to another function. This is how the classroom harness
invokes *your* implementation. The argument `candidate` below is a function object; parentheses
perform the call. Predict the two answers before execution, then trace the result to the callback.

```python tags=["foundation", "worked-example"]
def intro_apply(candidate, value):
    return {"input": value, "observed": candidate(value)}


def intro_double(value):
    return value * 2


print(intro_apply(intro_double, 3))
print(intro_apply(lambda value: value + 2, 3))
assert intro_apply(intro_double, 3)["observed"] == 6
```

`lambda value: value + 2` is a small anonymous function. A **closure** is a function that retains
access to values from its surrounding scope. It can bind a tool to a shop snapshot. A shallow
copy duplicates only the outer container; `copy.deepcopy` also copies nested containers used
in these fixtures. A **set** stores distinct values; `required <= allowed` asks whether every
required item is allowed. `frozenset` is the corresponding immutable set. A tuple groups ordered
values; `(value,)` is a one-item tuple, including the comma.

**Paths and cleanup.** `Path` represents a filesystem location. `path / "file.json"` constructs
a child path; `read_text` and `write_text` read and write text. A context manager, used with
`with`, manages entry and exit. A temporary-directory context removes its contents on exit.
Save your submission outside temporary runtime directories. Reopening a file is different from
reusing a Python variable: the former tests retained bytes, while the latter only tests this kernel.

```python tags=["foundation", "worked-example"]
from pathlib import Path
from tempfile import TemporaryDirectory

with TemporaryDirectory() as intro_folder:
    intro_path = Path(intro_folder) / "observation.json"
    intro_path.write_text(json.dumps(intro_data), encoding="utf-8")
    intro_reopened = json.loads(intro_path.read_text(encoding="utf-8"))
    assert intro_reopened == intro_data
    print("Read from a file:", intro_reopened)
```

**Retrieval check:** explain JSON versus a dictionary, annotation versus validation, class versus
instance, and defining a callback versus invoking it. Change the callback above so an incorrect
implementation visibly changes the observed output. This distinction will matter when grading
your connected work. Reference: Python's [JSON](https://docs.python.org/3.14/library/json.html),
[dataclasses](https://docs.python.org/3.14/library/dataclasses.html), and
[pathlib](https://docs.python.org/3.14/library/pathlib.html) documentation.
