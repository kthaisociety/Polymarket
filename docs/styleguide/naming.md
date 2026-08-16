# Naming

> General convention: clarity over compactness.

## Names carry domain meaning

Prefer a longer unambiguous name over an abbreviation readers must decode. Use the vocabulary defined
by the architecture and domain glossary.

Casing follows the language and configured linter.

## Functions name the operation

Use a verb and the object or outcome:

```python
load_dataset()
validate_time_index()
build_research_context()
record_episode_transition()
```

Avoid vague names such as `handle`, `process`, or `manage` when a precise operation is available.

Drop qualifiers already supplied by the module at the call site.

```python
datasets.load_catalog()       # not datasets.load_dataset_catalog()
artifacts.open_read_only()    # not artifacts.open_artifact_store_read_only()
```

## Variables use complete words

Name values for their meaning:

```python
observation_time
training_window
researcher_state
provider_response
```

Keep established short names when they are unambiguous in context, such as `rows`, `db`, or
`url`. Avoid single-letter variables outside conventional mathematical expressions or very small
local comprehensions.

## Distinguish identifiers from values

Use suffixes such as `_id`, `_path`, `_url`, and `_at` consistently when they clarify the
kind of value. Do not add a suffix that lies about the type.

## Closed values use closed types

Define a fixed value set once with a `Literal`, enum, or validated value type.

```python
DatasetFrequency = Literal["daily", "weekly", "monthly"]
```

Reuse the same definition across boundaries rather than duplicating allowed strings.
