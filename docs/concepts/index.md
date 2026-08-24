# Core concepts

## Sessions are directories

A session directory is the unit of state, recovery, audit, and portability.
There is no required database behind the core runtime.

## State moves forward

Completed history is not reopened. Retry and resume create linked child
sessions, preserving evidence.

## Tickets make operations auditable

Planner and executor work produces append-only tickets. Manifests record output
paths and hashes so later readers can detect changes.

## The loop proposes; structured code constrains

The loop half uses a model to plan and act. The structured half applies Python
rules, classifiers, or judges. Atomic file handoffs connect them.

## Capabilities are physics

Prompts can suggest behavior; the callable surface determines which actions
exist. ZeoCore capabilities define reusable domain actions. Sovereign runtime
commands control session behavior.

## “It ran” is not “it worked”

Structural checks prove calls and files exist. Dataflow integrity checks prove
the final result used capability outputs rather than inventing plausible facts.

Continue with the full [architecture](../architecture.md) or see these concepts
in the [tutorials](../tutorials/index.md).
