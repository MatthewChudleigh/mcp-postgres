---
description: Run a read-only SQL query against the configured Postgres database
argument-hint: <SQL SELECT statement>
---

Execute the following read-only SQL query using the `postgres` MCP server's `execute_sql` tool and present the results as a markdown table:

```sql
$ARGUMENTS
```

If the statement is not a SELECT/CTE read query, refuse and explain why.
