# Sprint v0.7 – Custom Schema Passthrough

## Objective
Create a method to include additional user-defined Workspace schemas in the Directory API fetch
and return their values raw in `EffectiveAuth`. The design must support all Google-allowed custom
field types and handle both single-value and multi-value fields with a consistent, easy-to-parse
shape.

## Deliverables
- Configuration to list additional schema names to fetch (beyond `GOOGLE_WORKSPACE_AUTH_SCHEMA`)
  via `GOOGLE_WORKSPACE_EXTRA_SCHEMAS`.
- `WorkspaceDirectoryClient` updates to include the extra schemas in `customFieldMask`.
- `EffectiveAuth` includes a new `custom_schemas` payload that mirrors the Workspace schema names.
- Normalization rules for custom field values covering all supported data types.
- Documentation and sample `.env` updates describing how to enable schema passthrough.
- Unit coverage for normalization of single-value and multi-value fields.

## Data Types
Supported types and expected raw shapes:
- text
- Whole Number
- Yes or No
- Decimal Number
- Phone
- Email
- Date

All types can be configured as single-value or multi-value in Google Workspace.

## Normalized Output Shape
Return values in a predictable structure:

```
custom_schemas: {
  "<SchemaName>": {
    "<FieldName>": {
      "type": "<google_type>",
      "multi": <bool>,
      "values": [<string>]
    }
  }
}
```

Normalization rules:
- Always return an array in `values`, even for single-value fields.
- Coerce all values to strings to keep a consistent format across types.
- Preserve schema and field names exactly as they appear in Workspace.

## Implementation Notes
- Add `GOOGLE_WORKSPACE_EXTRA_SCHEMAS` (comma-separated list).
- Merge these schema names into `WorkspaceDirectoryClient._build_custom_field_mask`.
- Add `custom_schemas` to `EffectiveAuth` without altering existing `permissions`/`functions`.
- If a schema is missing or empty for a user, return an empty object for that schema.
