# ManifestV1 Protocol

> Placeholder — full protocol specification coming soon.

## Fields

| Field | Type | Description |
|---|---|---|
| `run_id` | `str` | Unique identifier for the execution run |
| `step_index` | `int` | Zero-based index of this step in the chain |
| `agent_id` | `str` | Identifier of the agent that executed this step |
| `action` | `str` | Name of the action performed |
| `inputs` | `dict` | Input parameters for the step |
| `outputs` | `dict` | Output values produced by the step |
| `timestamp_utc` | `str` | ISO-8601 UTC timestamp |
| `previous_step_digest` | `str | None` | SHA-256 digest of the previous step manifest |
