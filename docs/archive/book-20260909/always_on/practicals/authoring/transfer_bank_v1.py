"""Authored changed-constraint tasks with independently specified expectations."""

TASKS = {
    1: {
        "title": "Check a brief after the catalog changes",
        "contract": (
            "Implement transfer_check(rows, claims). rows contains uniq"
            "ue sku, on_hand and target fields. claims maps SKU to clai"
            "med needed quantity. Return True only when claims contains"
            " exactly the positive deficits, with exact integer quantit"
            "ies; bool is not a quantity. Empty stock and empty claims "
            "agree. Do not mutate either input."
        ),
        "starter": (
            "def transfer_check(rows, claims):\n    raise NotImplemented"
            "Error('Compare every claimed deficit with the supplied cat"
            "alog')\n"
        ),
        "solution": (
            "def transfer_check(rows, claims):\n    expected = {r['sku']"
            ": max(0, r['target'] - r['on_hand']) for r in rows if r['t"
            "arget'] > r['on_hand']}\n    return isinstance(claims, dict"
            ") and set(claims) == set(expected) and all(type(claims[k])"
            " is int and claims[k] == v for k, v in expected.items())\n"
        ),
        "cases": [
            ("new mango", [[{"sku": "MANGO", "on_hand": 1, "target": 5}], {"MANGO": 4}], True),
            (
                "fluent wrong number",
                [[{"sku": "MANGO", "on_hand": 1, "target": 5}], {"MANGO": 3}],
                False,
            ),
            ("exact empty", [[], {}], True),
            ("invented product", [[], {"MANGO": 4}], False),
        ],
        "holdouts": [
            ("boolean one", [[{"sku": "PEAR", "on_hand": 2, "target": 3}], {"PEAR": True}], False),
            ("surplus omitted", [[{"sku": "PEAR", "on_hand": 8, "target": 3}], {}], True),
            (
                "zero entry violates output shape",
                [[{"sku": "PEAR", "on_hand": 8, "target": 3}], {"PEAR": 0}],
                False,
            ),
        ],
        "reason": (
            "Calculate deficits from the catalog, then compare both ide"
            "ntities and values. Checking only the grand total cannot d"
            "etect missing or substituted products. A successful check "
            "supports these structured claims, not arbitrary prose."
        ),
    },
    2: {
        "title": "Use one reservation rule in reporting and drafting",
        "contract": (
            "Implement transfer_check(row). Return max(0, target - on_h"
            "and + reserved), treating an absent reserved field as zero"
            ". Inputs are validated nonnegative integers. The driver us"
            "es your result for both the stock report and the exact-qua"
            "ntity draft decision; changing your function must change b"
            "oth."
        ),
        "starter": (
            "def transfer_check(row):\n    raise NotImplementedError('Ca"
            "lculate sellable stock before the deficit')\n"
        ),
        "solution": (
            "def transfer_check(row):\n    return max(0, row['target'] -"
            " row['on_hand'] + row.get('reserved', 0))\n"
        ),
        "cases": [
            ("reserved mango", [{"on_hand": 1, "target": 5, "reserved": 2}], 6),
            ("no reservations field", [{"on_hand": 1, "target": 5}], 4),
            ("surplus", [{"on_hand": 12, "target": 6, "reserved": 2}], 0),
            ("exact sellable target", [{"on_hand": 7, "target": 5, "reserved": 2}], 0),
        ],
        "holdouts": [
            ("reservations exceed physical", [{"on_hand": 2, "target": 5, "reserved": 8}], 11),
            ("new boundary", [{"on_hand": 10, "target": 6, "reserved": 5}], 1),
        ],
        "reason": (
            "Available stock is on_hand minus reserved. Substitute that"
            " expression into target minus available, then clamp at zer"
            "o. Reusing the function prevents a report from saying six "
            "while a draft validator still demands four."
        ),
    },
    3: {
        "title": "Admit a variable-cost next model attempt",
        "contract": (
            "Implement transfer_check(state). Fields calls, max_calls, "
            "spent, next_cost and budget are validated nonnegative inte"
            "gers. Return CALL_LIMIT first when calls >= max_calls, oth"
            "erwise COST_LIMIT when spent + next_cost > budget, otherwi"
            "se CALL. Equality at the money boundary is allowed. The ne"
            "xt-cost estimate can differ on every attempt."
        ),
        "starter": (
            "def transfer_check(state):\n    raise NotImplementedError('"
            "Decide before admitting the next attempt')\n"
        ),
        "solution": (
            "def transfer_check(state):\n    if state['calls'] >= state["
            "'max_calls']:\n        return 'CALL_LIMIT'\n    if state['sp"
            "ent'] + state['next_cost'] > state['budget']:\n        retu"
            "rn 'COST_LIMIT'\n    return 'CALL'\n"
        ),
        "cases": [
            (
                "exact fit",
                [{"calls": 1, "max_calls": 3, "spent": 4, "next_cost": 3, "budget": 7}],
                "CALL",
            ),
            (
                "next attempt too costly",
                [{"calls": 1, "max_calls": 3, "spent": 4, "next_cost": 4, "budget": 7}],
                "COST_LIMIT",
            ),
            (
                "two exhausted limits",
                [{"calls": 3, "max_calls": 3, "spent": 7, "next_cost": 1, "budget": 7}],
                "CALL_LIMIT",
            ),
            (
                "zero allowed attempts",
                [{"calls": 0, "max_calls": 0, "spent": 0, "next_cost": 0, "budget": 0}],
                "CALL_LIMIT",
            ),
        ],
        "holdouts": [
            (
                "free but counted attempt",
                [{"calls": 2, "max_calls": 3, "spent": 7, "next_cost": 0, "budget": 7}],
                "CALL",
            ),
            (
                "new estimate",
                [{"calls": 0, "max_calls": 8, "spent": 0, "next_cost": 11, "budget": 10}],
                "COST_LIMIT",
            ),
        ],
        "reason": (
            "Admission concerns the next exposure, not only what was al"
            "ready spent. A failed admitted attempt is still charged by"
            " the caller. Keep the decision and the accounting event di"
            "stinct in the trace."
        ),
    },
    4: {
        "title": "Retrieve the newest eligible memory under a limit",
        "contract": (
            "Implement transfer_check(rows, session, limit). Each row h"
            "as unique integer id, session and boolean active. Return e"
            "ligible row IDs newest first, at most limit. Require an ex"
            "act integer limit in 1..100; otherwise raise ValueError. E"
            "mpty eligible input returns an empty list. Do not mutate r"
            "ows. This deliberately isolates eligibility and tie order "
            "from lexical scoring."
        ),
        "starter": (
            "def transfer_check(rows, session, limit):\n    raise NotImp"
            "lementedError('Filter before ordering and limiting')\n"
        ),
        "solution": (
            "def transfer_check(rows, session, limit):\n    if type(limi"
            "t) is not int or not 1 <= limit <= 100:\n        raise Valu"
            "eError('invalid limit')\n    return sorted((r['id'] for r i"
            "n rows if r['session'] == session and r['active']), revers"
            "e=True)[:limit]\n"
        ),
        "cases": [
            (
                "current own row",
                [
                    [
                        {"id": 1, "session": "lucy", "active": False},
                        {"id": 2, "session": "lucy", "active": True},
                        {"id": 3, "session": "other", "active": True},
                    ],
                    "lucy",
                    2,
                ],
                [2],
            ),
            (
                "newest first",
                [
                    [
                        {"id": 8, "session": "lucy", "active": True},
                        {"id": 9, "session": "lucy", "active": True},
                    ],
                    "lucy",
                    1,
                ],
                [9],
            ),
            ("empty", [[], "lucy", 3], []),
            ("zero limit", [[], "lucy", 0], {"raises": "ValueError"}),
        ],
        "holdouts": [
            ("bool limit", [[], "lucy", True], {"raises": "ValueError"}),
            ("upper limit", [[], "lucy", 101], {"raises": "ValueError"}),
            (
                "renamed session",
                [[{"id": 22, "session": "pear-shop", "active": True}], "pear-shop", 100],
                [22],
            ),
        ],
        "reason": (
            "Filtering excludes foreign and superseded rows before the "
            "budget is spent. A valid empty result differs from an inva"
            "lid requested limit. Deterministic ordering makes a repeat"
            "ed retrieval explainable."
        ),
    },
    5: {
        "title": "Admit only complete skill requirements",
        "contract": (
            "Implement transfer_check(skills, allowed). Return names, p"
            "reserving input order, for skills with active=True whose c"
            "omplete requires list is a subset of allowed. Inputs have "
            "unique names. An empty requirement list is eligible even w"
            "hen allowed is empty. Never change allowed based on instru"
            "ction text."
        ),
        "starter": (
            "def transfer_check(skills, allowed):\n    raise NotImplemen"
            "tedError('Separate active state from capability eligibilit"
            "y')\n"
        ),
        "solution": (
            "def transfer_check(skills, allowed):\n    return [s['name']"
            " for s in skills if s['active'] and set(s['requires']) <= "
            "set(allowed)]\n"
        ),
        "cases": [
            (
                "partial capabilities",
                [[{"name": "opening", "active": True, "requires": ["stock", "price"]}], ["stock"]],
                [],
            ),
            (
                "all capabilities",
                [
                    [{"name": "opening", "active": True, "requires": ["stock", "price"]}],
                    ["stock", "price"],
                ],
                ["opening"],
            ),
            (
                "empty requirements",
                [[{"name": "greeting", "active": True, "requires": []}], []],
                ["greeting"],
            ),
            ("staged only", [[{"name": "greeting", "active": False, "requires": []}], []], []),
        ],
        "holdouts": [
            ("empty skills", [[], ["stock"]], []),
            (
                "stable input order",
                [
                    [
                        {"name": "z", "active": True, "requires": []},
                        {"name": "a", "active": True, "requires": []},
                    ],
                    [],
                ],
                ["z", "a"],
            ),
        ],
        "reason": (
            "Intersection answers whether at least one capability overl"
            "aps. Subset answers whether every requirement is available"
            ". Neither parsing nor active status replaces that complete"
            " requirement check."
        ),
    },
    6: {
        "title": "Plan private intake across accounts and replays",
        "contract": (
            "Implement transfer_check(updates, seen, allowed). Return n"
            "ew [account, update_id] pairs in input order for private m"
            "essages with exact integer sender/chat IDs, matching sende"
            "r and chat, sender in allowed, and nonempty text of at mos"
            "t 100 characters. seen contains prior [account, update_id]"
            " pairs. Deduplicate within the batch too. Updates have val"
            "id account strings and integer update IDs; refuse ineligib"
            "le messages by omission. Do not mutate inputs."
        ),
        "starter": (
            "def transfer_check(updates, seen, allowed):\n    raise NotI"
            "mplementedError('Bind private identity before deduplicatin"
            "g intake')\n"
        ),
        "solution": (
            "def transfer_check(updates, seen, allowed):\n    known = {t"
            "uple(item) for item in seen}\n    result = []\n    for u in "
            "updates:\n        identity = (u['account'], u['id'])\n      "
            "  eligible = type(u['sender']) is int and type(u['chat']) "
            "is int and u['sender'] == u['chat'] and u['sender'] in all"
            "owed and u['kind'] == 'private' and isinstance(u['text'], "
            "str) and 1 <= len(u['text']) <= 100\n        if eligible an"
            "d identity not in known:\n            result.append(list(id"
            "entity))\n            known.add(identity)\n    return result"
            "\n"
        ),
        "cases": [
            (
                "private",
                [
                    [
                        {
                            "account": "a",
                            "id": 1,
                            "sender": 7,
                            "chat": 7,
                            "kind": "private",
                            "text": "Hello",
                        }
                    ],
                    [],
                    [7],
                ],
                [["a", 1]],
            ),
            (
                "group",
                [
                    [
                        {
                            "account": "a",
                            "id": 1,
                            "sender": 7,
                            "chat": -1,
                            "kind": "group",
                            "text": "Hello",
                        }
                    ],
                    [],
                    [7],
                ],
                [],
            ),
            (
                "already retained",
                [
                    [
                        {
                            "account": "a",
                            "id": 1,
                            "sender": 7,
                            "chat": 7,
                            "kind": "private",
                            "text": "Hello",
                        }
                    ],
                    [["a", 1]],
                    [7],
                ],
                [],
            ),
            (
                "different account",
                [
                    [
                        {
                            "account": "b",
                            "id": 1,
                            "sender": 7,
                            "chat": 7,
                            "kind": "private",
                            "text": "Hello",
                        }
                    ],
                    [["a", 1]],
                    [7],
                ],
                [["b", 1]],
            ),
        ],
        "holdouts": [
            (
                "boolean identity",
                [
                    [
                        {
                            "account": "a",
                            "id": 2,
                            "sender": True,
                            "chat": True,
                            "kind": "private",
                            "text": "Hi",
                        }
                    ],
                    [],
                    [1],
                ],
                [],
            ),
            ("empty batch", [[], [], [7]], []),
            (
                "empty content",
                [
                    [
                        {
                            "account": "a",
                            "id": 3,
                            "sender": 7,
                            "chat": 7,
                            "kind": "private",
                            "text": "",
                        }
                    ],
                    [],
                    [7],
                ],
                [],
            ),
        ],
        "reason": (
            "The origin is account plus update ID. Private-chat admissi"
            "on precedes creation of work. A replayed transport batch c"
            "an contain both old and new eligible updates; neither blan"
            "ket acceptance nor blanket refusal implements that distinc"
            "tion."
        ),
    },
    7: {
        "title": "Coalesce while preserving a deferred due job",
        "contract": (
            "Implement transfer_check(due, interval, now, capacity). In"
            "puts are finite numbers with positive interval and nonnega"
            "tive integer capacity. Return [created, next_due, skipped]"
            ". Before due or at zero capacity, return [0, due, 0]. Othe"
            "rwise create one occurrence, count skipped whole intervals"
            ", and advance next_due strictly beyond now. Do not use sle"
            "ep or the actual clock."
        ),
        "starter": (
            "def transfer_check(due, interval, now, capacity):\n    rais"
            "e NotImplementedError('Plan one bounded scheduler pass')\n"
        ),
        "solution": (
            "def transfer_check(due, interval, now, capacity):\n    if n"
            "ow < due or capacity == 0:\n        return [0, due, 0]\n    "
            "skipped = int((now - due) // interval)\n    return [1, due "
            "+ (skipped + 1) * interval, skipped]\n"
        ),
        "cases": [
            ("before due", [10, 5, 9, 1], [0, 10, 0]),
            ("exact due", [10, 5, 10, 1], [1, 15, 0]),
            ("long absence", [10, 5, 22, 1], [1, 25, 2]),
            ("queue full retains due", [10, 5, 22, 0], [0, 10, 0]),
        ],
        "holdouts": [
            ("fractional interval", [0.5, 0.25, 1.0, 4], [1, 1.25, 2]),
            ("very long absence", [0, 10, 100000, 1], [1, 100010, 10000]),
        ],
        "reason": (
            "Advancing by one interval after a long absence leaves the "
            "job due. Advancing when capacity is zero loses the deferre"
            "d occurrence. Both timing and admission outcome must deter"
            "mine the stored next time."
        ),
    },
    8: {
        "title": "Apply the stricter cumulative spending ceiling",
        "contract": (
            "Implement transfer_check(spent, reserved, addition, instal"
            "led, supplied). All values must be exact nonnegative integ"
            "ers; otherwise raise ValueError. Return whether spent + re"
            "served + addition is at most min(installed, supplied). A r"
            "epeated already-reserved approval passes addition=0. Do no"
            "t interpret this arithmetic result as actor approval or su"
            "pplier evidence."
        ),
        "starter": (
            "def transfer_check(spent, reserved, addition, installed, s"
            "upplied):\n    raise NotImplementedError('Compare cumulativ"
            "e exposure to both ceilings')\n"
        ),
        "solution": (
            "def transfer_check(spent, reserved, addition, installed, s"
            "upplied):\n    values = (spent, reserved, addition, install"
            "ed, supplied)\n    if any(type(v) is not int or v < 0 for v"
            " in values):\n        raise ValueError('nonnegative integer"
            " pence required')\n    return spent + reserved + addition <"
            "= min(installed, supplied)\n"
        ),
        "cases": [
            ("exact fit", [700, 900, 400, 2000, 2500], True),
            ("one penny too many", [700, 900, 401, 2000, 2500], False),
            ("stricter supplied policy", [700, 900, 100, 2000, 1600], False),
            ("no double reservation", [700, 900, 0, 2000, 1600], True),
        ],
        "holdouts": [
            ("negative addition", [0, 0, -1, 100, 100], {"raises": "ValueError"}),
            ("boolean money", [0, 0, True, 100, 100], {"raises": "ValueError"}),
            ("zero ceiling", [0, 0, 0, 0, 0], True),
        ],
        "reason": (
            "Check every monetary input before arithmetic. Reserved and"
            " spent both consume authority. The smaller ceiling prevent"
            "s a caller from widening installed policy, while zero addi"
            "tion makes repeated approval accounting explicit."
        ),
    },
    9: {
        "title": "Interpret discovery without inventing certainty",
        "contract": (
            "Implement transfer_check(operation, proposal, receipt). No"
            "ne means UNKNOWN. Otherwise require a dictionary whose ope"
            "ration equals the intended operation and proposal equals t"
            "he exact proposal. ACCEPTED maps to CONFIRMED; REJECTED ma"
            "ps to REJECTED. Any other receipt or decision raises Value"
            "Error. Do not alter the proposal or assign a new operation"
            " ID."
        ),
        "starter": (
            "def transfer_check(operation, proposal, receipt):\n    rais"
            "e NotImplementedError('Require matching conclusive supplie"
            "r evidence')\n"
        ),
        "solution": (
            "def transfer_check(operation, proposal, receipt):\n    if r"
            "eceipt is None:\n        return 'UNKNOWN'\n    if not isinst"
            "ance(receipt, dict) or receipt.get('operation') != operati"
            "on or receipt.get('proposal') != proposal:\n        raise V"
            "alueError('receipt identity mismatch')\n    if receipt.get("
            "'status') == 'ACCEPTED':\n        return 'CONFIRMED'\n    if"
            " receipt.get('status') == 'REJECTED':\n        return 'REJE"
            "CTED'\n    raise ValueError('inconclusive receipt')\n"
        ),
        "cases": [
            ("no evidence", ["op-a", {"quantity": 4}, None], "UNKNOWN"),
            (
                "accepted evidence",
                [
                    "op-a",
                    {"quantity": 4},
                    {"operation": "op-a", "proposal": {"quantity": 4}, "status": "ACCEPTED"},
                ],
                "CONFIRMED",
            ),
            (
                "new identity",
                [
                    "op-a",
                    {"quantity": 4},
                    {"operation": "op-b", "proposal": {"quantity": 4}, "status": "ACCEPTED"},
                ],
                {"raises": "ValueError"},
            ),
            (
                "changed quantity",
                [
                    "op-a",
                    {"quantity": 4},
                    {"operation": "op-a", "proposal": {"quantity": 5}, "status": "ACCEPTED"},
                ],
                {"raises": "ValueError"},
            ),
        ],
        "holdouts": [
            (
                "conclusive rejection",
                ["new", {}, {"operation": "new", "proposal": {}, "status": "REJECTED"}],
                "REJECTED",
            ),
            (
                "pending is not rejection",
                ["new", {}, {"operation": "new", "proposal": {}, "status": "PENDING"}],
                {"raises": "ValueError"},
            ),
            ("malformed receipt", ["new", {}, []], {"raises": "ValueError"}),
        ],
        "reason": (
            "Receipt identity, payload and conclusive status are indepe"
            "ndent requirements. An absent lookup remains unknown. Rena"
            "ming a pending state to rejected would release authority w"
            "ithout evidence."
        ),
    },
    10: {
        "title": "Explain admission across an authority replacement",
        "contract": (
            "Implement transfer_check(current, claim, now). Current con"
            "tains paused, epoch, generation, work and worker. Claim co"
            "ntains matching identity fields and lease_until. Return Tr"
            "ue only if current is not paused, all four identity fields"
            " match, and lease_until > now. These inputs are already sh"
            "ape-validated. Equality at expiry is refused."
        ),
        "starter": (
            "def transfer_check(current, claim, now):\n    raise NotImpl"
            "ementedError('Bind the full identity and unexpired lease')"
            "\n"
        ),
        "solution": (
            "def transfer_check(current, claim, now):\n    return not cu"
            "rrent['paused'] and all(current[k] == claim[k] for k in ('"
            "epoch', 'generation', 'work', 'worker')) and claim['lease_"
            "until'] > now\n"
        ),
        "cases": [],
        "holdouts": [],
        "reason": (
            "A matching worker name is insufficient. Each authority fie"
            "ld and the lease boundary must remain current. Positive an"
            "d one-field-stale cases prevent one check from hiding the "
            "absence of another."
        ),
    },
    11: {
        "title": "Separate registration, permission and consequential authority",
        "contract": (
            "Implement transfer_check(name, registered, allowed, conseq"
            "uential, has_authority). Return True only for a name in bo"
            "th registered and allowed and, if consequential is True, w"
            "ith has_authority=True. Inputs are validated names, lists "
            "and booleans. The driver records an effect only when your "
            "function admits it; compare effects as well as decisions."
        ),
        "starter": (
            "def transfer_check(name, registered, allowed, consequentia"
            "l, has_authority):\n    raise NotImplementedError('Admit be"
            "fore the handler effect')\n"
        ),
        "solution": (
            "def transfer_check(name, registered, allowed, consequentia"
            "l, has_authority):\n    return name in registered and name "
            "in allowed and (not consequential or has_authority)\n"
        ),
        "cases": [
            ("allowed read", ["stock", ["stock"], ["stock"], False, False], True),
            ("registered forbidden", ["stock", ["stock"], [], False, False], False),
            ("unregistered advertised", ["buy", [], ["buy"], True, True], False),
            ("write lacks authority", ["buy", ["buy"], ["buy"], True, False], False),
        ],
        "holdouts": [
            ("authorized write", ["buy", ["buy"], ["buy"], True, True], True),
            ("new allowed tool", ["quote", ["stock", "quote"], ["quote"], False, False], True),
        ],
        "reason": (
            "The permission decision must precede invocation. A known n"
            "ame is not sufficient authority, and an allowed name witho"
            "ut an implementation is not callable. OS containment remai"
            "ns a different boundary."
        ),
    },
    12: {
        "title": "Build an oracle that cannot copy the expected answer",
        "contract": (
            "Implement transfer_check(rows). Each row has sku, physical"
            ", reserved and target nonnegative integer fields. Return a"
            " dictionary of only positive deficits, calculated from phy"
            "sical minus reserved. There is deliberately no expected fi"
            "eld in this interface. Inputs have unique identities and m"
            "ust remain unchanged."
        ),
        "starter": (
            "def transfer_check(rows):\n    raise NotImplementedError('C"
            "alculate independent deficits from stock inputs')\n"
        ),
        "solution": (
            "def transfer_check(rows):\n    return {r['sku']: r['target'"
            "] - r['physical'] + r['reserved'] for r in rows if r['targ"
            "et'] > r['physical'] - r['reserved']}\n"
        ),
        "cases": [
            (
                "reserved deficit",
                [[{"sku": "MANGO", "physical": 6, "reserved": 4, "target": 5}]],
                {"MANGO": 3},
            ),
            (
                "exact threshold",
                [[{"sku": "MANGO", "physical": 7, "reserved": 2, "target": 5}]],
                {},
            ),
            ("empty", [[]], {}),
            (
                "renamed identity",
                [[{"sku": "PEAR", "physical": 1, "reserved": 0, "target": 4}]],
                {"PEAR": 3},
            ),
        ],
        "holdouts": [
            (
                "overreserved",
                [[{"sku": "NEW", "physical": 1, "reserved": 9, "target": 3}]],
                {"NEW": 11},
            ),
            ("surplus", [[{"sku": "NEW", "physical": 10, "reserved": 1, "target": 3}]], {}),
        ],
        "reason": (
            "Expected values are authored before candidate execution. R"
            "emoving the expected-answer field from the candidate inter"
            "face makes that particular shortcut unavailable, while cha"
            "nged identities challenge fixture lookup."
        ),
    },
    13: {
        "title": "Admit activation only against complete current evidence",
        "contract": (
            "Implement transfer_check(before, current, results, require"
            "d). Return True only if required is nonempty, all required"
            " case names exist in results with value exactly True, and "
            "the active configuration dictionaries before/current are e"
            "qual. Do not mutate any input. Extra observed cases are pe"
            "rmitted but do not replace required cases."
        ),
        "starter": (
            "def transfer_check(before, current, results, required):\n  "
            "  raise NotImplementedError('Bind evaluation coverage to t"
            "he current configuration')\n"
        ),
        "solution": (
            "def transfer_check(before, current, results, required):\n  "
            "  return bool(required) and before == current and all(name"
            " in results and results[name] is True for name in required"
            ")\n"
        ),
        "cases": [
            (
                "current positive",
                [
                    {"opening": 2},
                    {"opening": 2},
                    {"normal": True, "reserved": True},
                    ["normal", "reserved"],
                ],
                True,
            ),
            (
                "stale baseline",
                [{"opening": 2}, {"opening": 3}, {"normal": True}, ["normal"]],
                False,
            ),
            ("missing case", [{}, {}, {"normal": True}, ["normal", "reserved"]], False),
            ("truthy integer", [{}, {}, {"normal": 1}, ["normal"]], False),
        ],
        "holdouts": [
            ("empty required suite", [{}, {}, {}, []], False),
            ("extra case permitted", [{}, {}, {"normal": True, "new": False}, ["normal"]], True),
            ("explicit failed case", [{}, {}, {"normal": False}, ["normal"]], False),
        ],
        "reason": (
            "Empty coverage and truthy non-booleans are not positive ev"
            "idence. A complete positive evaluation can still be stale."
            " The final equality belongs in the activation transaction "
            "in the real mechanism."
        ),
    },
    14: {
        "title": "Change the supplier's portions per tub",
        "contract": (
            "Implement transfer_check(guests, price_pence, portions). R"
            "equire exact positive integers for all three inputs, other"
            "wise raise ValueError. Return [tubs, total_pence], using c"
            "eiling division. The new portions argument replaces the ea"
            "rlier fixed ten-portion assumption. No stock or approval s"
            "tate changes."
        ),
        "starter": (
            "def transfer_check(guests, price_pence, portions):\n    rai"
            "se NotImplementedError('Validate and round the changed pac"
            "k size upward')\n"
        ),
        "solution": (
            "def transfer_check(guests, price_pence, portions):\n    if "
            "any(type(v) is not int or v <= 0 for v in (guests, price_p"
            "ence, portions)):\n        raise ValueError('positive integ"
            "ers required')\n    tubs = (guests + portions - 1) // porti"
            "ons\n    return [tubs, tubs * price_pence]\n"
        ),
        "cases": [
            ("eleven guests", [11, 325, 10], [2, 650]),
            ("exact eight portion tub", [16, 275, 8], [2, 550]),
            ("partial new tub", [17, 275, 8], [3, 825]),
            ("zero portions", [17, 275, 0], {"raises": "ValueError"}),
        ],
        "holdouts": [
            ("one guest", [1, 399, 12], [1, 399]),
            ("boolean guests", [True, 325, 10], {"raises": "ValueError"}),
            ("large exact group", [200, 300, 10], [20, 6000]),
        ],
        "reason": (
            "A change in portions is a real contract change. Derive cei"
            "ling division with the supplied denominator, validate befo"
            "re dividing, and multiply in integer pence. The result is "
            "still a draft."
        ),
    },
    15: {
        "title": "Validate every member of a restore manifest",
        "contract": (
            "Implement transfer_check(expected, observed). These dictio"
            "naries map relative file names to already-computed digest "
            "strings. Return True only when expected is nonempty, names"
            " match exactly, and every digest matches. Missing and unex"
            "pected files both refuse. This checks manifest agreement, "
            "not schema compatibility or external freshness."
        ),
        "starter": (
            "def transfer_check(expected, observed):\n    raise NotImple"
            "mentedError('Compare complete manifest membership and dige"
            "sts')\n"
        ),
        "solution": (
            "def transfer_check(expected, observed):\n    return bool(ex"
            "pected) and set(expected) == set(observed) and all(observe"
            "d[name] == value for name, value in expected.items())\n"
        ),
        "cases": [
            ("intact", [{"db": "a", "authority": "b"}, {"authority": "b", "db": "a"}], True),
            ("missing authority", [{"db": "a", "authority": "b"}, {"db": "a"}], False),
            ("changed database", [{"db": "a"}, {"db": "different"}], False),
            ("unexpected member", [{"db": "a"}, {"db": "a", "extra": "b"}], False),
        ],
        "holdouts": [
            ("empty manifest", [{}, {}], False),
            (
                "new names",
                [
                    {"snapshot.sqlite": "c", "epoch.txt": "d"},
                    {"snapshot.sqlite": "c", "epoch.txt": "d"},
                ],
                True,
            ),
        ],
        "reason": (
            "Checking only observed files misses an absent member. Chec"
            "king only expected files misses an unexpected member. Exac"
            "t set equality plus value comparison establishes this narr"
            "ow integrity contract."
        ),
    },
    16: {
        "title": "Reconcile an independently supplied order ledger",
        "contract": (
            "Implement transfer_check(orders, ledger). Orders contain u"
            "nique id, status and nonnegative integer amount. Sum reser"
            "ved for APPROVED/SENDING/UNKNOWN and spent for CONFIRMED/D"
            "ELIVERED; DRAFT/REJECTED contribute neither. Raise ValueEr"
            "ror on any other status. Return {matches: bool, reserved: "
            "int, spent: int, unknown: sorted IDs}. Ledger contains res"
            "erved/spent totals. Do not replace missing evidence with i"
            "nvented money."
        ),
        "starter": (
            "def transfer_check(orders, ledger):\n    raise NotImplement"
            "edError('Compute order evidence before comparing the ledge"
            "r')\n"
        ),
        "solution": (
            "def transfer_check(orders, ledger):\n    reserved = spent ="
            " 0\n    unknown = []\n    for row in orders:\n        status "
            "= row['status']\n        if status in {'APPROVED', 'SENDING"
            "', 'UNKNOWN'}:\n            reserved += row['amount']\n     "
            "   elif status in {'CONFIRMED', 'DELIVERED'}:\n            "
            "spent += row['amount']\n        elif status not in {'DRAFT'"
            ", 'REJECTED'}:\n            raise ValueError('unrecognized "
            "order state')\n        if status == 'UNKNOWN':\n            "
            "unknown.append(row['id'])\n    return {'matches': ledger =="
            " {'reserved': reserved, 'spent': spent}, 'reserved': reser"
            "ved, 'spent': spent, 'unknown': sorted(unknown)}\n"
        ),
        "cases": [
            (
                "uncertain and confirmed",
                [
                    [
                        {"id": "a", "status": "CONFIRMED", "amount": 1500},
                        {"id": "b", "status": "UNKNOWN", "amount": 1100},
                    ],
                    {"reserved": 1100, "spent": 1500},
                ],
                {"matches": True, "reserved": 1100, "spent": 1500, "unknown": ["b"]},
            ),
            (
                "ledger disagreement",
                [
                    [{"id": "b", "status": "UNKNOWN", "amount": 1100}],
                    {"reserved": 1000, "spent": 0},
                ],
                {"matches": False, "reserved": 1100, "spent": 0, "unknown": ["b"]},
            ),
            (
                "empty day",
                [[], {"reserved": 0, "spent": 0}],
                {"matches": True, "reserved": 0, "spent": 0, "unknown": []},
            ),
            (
                "unrecognized state",
                [[{"id": "c", "status": "MAYBE", "amount": 5}], {"reserved": 0, "spent": 0}],
                {"raises": "ValueError"},
            ),
        ],
        "holdouts": [
            (
                "rejection contributes nothing",
                [[{"id": "r", "status": "REJECTED", "amount": 500}], {"reserved": 0, "spent": 0}],
                {"matches": True, "reserved": 0, "spent": 0, "unknown": []},
            ),
            (
                "delivered is retained spending",
                [
                    [{"id": "d", "status": "DELIVERED", "amount": 275}],
                    {"reserved": 0, "spent": 275},
                ],
                {"matches": True, "reserved": 0, "spent": 275, "unknown": []},
            ),
        ],
        "reason": (
            "Totals come from order rows before comparison with the ind"
            "ependent ledger. Retain unknown identities even when money"
            " agrees. Unknown status vocabulary must be investigated ra"
            "ther than treated as zero."
        ),
    },
}

# Explicitly varied identities isolate individual authority checks.
CURRENT = {"paused": False, "epoch": "new", "generation": 4, "work": "opening", "worker": "w1"}
CLAIM = {"epoch": "new", "generation": 4, "work": "opening", "worker": "w1", "lease_until": 20}
TASKS[10]["cases"] = [
    ("current claim", [CURRENT, CLAIM, 10], True),
    ("old epoch", [CURRENT, {**CLAIM, "epoch": "old"}, 10], False),
    ("old generation", [CURRENT, {**CLAIM, "generation": 3}, 10], False),
    ("exact expiry", [CURRENT, CLAIM, 20], False),
]
TASKS[10]["holdouts"] = [
    ("paused", [{**CURRENT, "paused": True}, CLAIM, 10], False),
    ("other work", [CURRENT, {**CLAIM, "work": "delivery"}, 10], False),
    ("other worker", [CURRENT, {**CLAIM, "worker": "w2"}, 10], False),
]
