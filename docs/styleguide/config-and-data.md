# Config and data

> General conventions for configuration, secrets, and data boundaries.

## Required configuration fails fast

Do not silently invent a fallback for required configuration. Validate required values during
startup and report missing or invalid values clearly.

Defaults are appropriate only when they are part of the documented product behavior. Keep those
defaults in the configuration layer rather than scattering them through application code.

## Keep one source of truth

Define each configuration value in one authoritative place. Derive transport-specific forms at the
boundary instead of duplicating hostnames, ports, paths, or timeouts across code and deployment
files.

## Keep secrets outside version control

Store credentials and tokens in the approved secret mechanism for the environment. Commit example
names and setup instructions, never real secret values. Avoid logging secrets or including them in
error messages, fixtures, snapshots, or generated artifacts.

## Make units explicit

Represent units with semantic types where practical. When a text format only supports raw numbers,
state the unit beside the value and convert it once at the loading boundary.

Do not encode units inconsistently in several names, comments, and conversion helpers.

## Validate data at boundaries

Treat external files, APIs, model responses, and database rows as untrusted inputs. Parse and
validate them at the boundary, then pass typed internal values through the rest of the system.

Preserve enough source and provenance information to reproduce how an internal value was derived.
Do not mutate source data in place when reproducibility depends on retaining the original input.

## Keep executable queries separate when a database is used

If the project adopts SQL, prefer named query files and bound parameters over SQL assembled from
user-controlled strings. The repository's database design will define the eventual query layout and
executor. This guide does not prescribe paths or a database product.
