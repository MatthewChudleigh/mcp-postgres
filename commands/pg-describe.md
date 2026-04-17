---
description: Describe a Postgres table (columns, types, keys)
argument-hint: <[schema.]table_name>
---

Use the `postgres` MCP server tools to describe `$ARGUMENTS`: first call `get_object_details` with the schema and table name to get columns, types, constraints, and indexes. Present as a concise markdown summary.
