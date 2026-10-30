# Chronos data

Chronos does not vendor a Polymarket database or committed contract tape.

The Polymarket source adapter reads exact facts through local parameterized, SELECT-only database
queries. Research registrations are derived in memory and carry contract, outcome, print, event
time, availability rule, block vintage, and source provenance. Production access uses the approved
`human_ro` tunnel and must prove that the role is read-only.

Do not place DSNs, passwords, database dumps, or ad hoc CSV exports here.
