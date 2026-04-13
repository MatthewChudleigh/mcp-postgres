import re
from dataclasses import dataclass
from typing import Any

# Valid unquoted SQL identifier: starts with letter or underscore, contains only alphanumeric/underscore
_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

# Valid index method names in PostgreSQL
_VALID_INDEX_METHODS = frozenset({"btree", "hash", "gist", "spgist", "gin", "brin"})

# Allowed characters in column expressions (for functional indexes like LOWER(col))
_COLUMN_EXPR_RE = re.compile(r"^[A-Za-z0-9_(),. ]+$")


def _validate_identifier(value: str, label: str) -> str:
    """Validate that a value is a safe SQL identifier."""
    if not value or not _IDENTIFIER_RE.match(value):
        raise ValueError(f"Invalid {label}: {value!r}. Must match [A-Za-z_][A-Za-z0-9_]*")
    return value


def _quote_identifier(value: str) -> str:
    """Quote a SQL identifier to prevent injection."""
    _validate_identifier(value, "identifier")
    return f'"{value}"'


def _validate_column_expr(value: str) -> str:
    """Validate a column expression (may include function calls like LOWER(col))."""
    if not value or not _COLUMN_EXPR_RE.match(value):
        raise ValueError(f"Invalid column expression: {value!r}. Contains disallowed characters.")
    return value


@dataclass(frozen=True)
class IndexDefinition:
    """Immutable index configuration for hashing."""

    table: str
    columns: tuple[str, ...]
    using: str = "btree"

    def __post_init__(self):
        _validate_identifier(self.table, "table name")
        if self.using not in _VALID_INDEX_METHODS:
            raise ValueError(f"Invalid index method: {self.using!r}. Must be one of {sorted(_VALID_INDEX_METHODS)}")
        if not self.columns:
            raise ValueError("Index must have at least one column")
        for col in self.columns:
            _validate_column_expr(col)

    def to_dict(self) -> dict[str, Any]:
        return {
            "table": self.table,
            "columns": list(self.columns),
            "using": self.using,
            "definition": self.definition,
        }

    @property
    def definition(self) -> str:
        quoted_table = _quote_identifier(self.table)
        quoted_columns = ", ".join(_quote_identifier(c) if _IDENTIFIER_RE.match(c) else c for c in self.columns)
        return f"CREATE INDEX {self.name} ON {quoted_table} USING {self.using} ({quoted_columns})"

    @property
    def name(self) -> str:
        # Clean column names for use in index naming
        # Replace special characters with underscores to avoid issues with
        # functional expressions
        cleaned_columns = []
        for col in self.columns:
            # Replace parentheses and other special characters with underscores
            # This ensures expressions like LOWER(column_name) work in
            # index names
            cleaned_col = col.replace("(", "_").replace(")", "_").replace(" ", "_").replace(",", "_")
            # Remove consecutive underscores
            while "__" in cleaned_col:
                cleaned_col = cleaned_col.replace("__", "_")
            # Remove trailing underscores
            cleaned_col = cleaned_col.rstrip("_")
            cleaned_columns.append(cleaned_col)

        column_part = "_".join(cleaned_columns)
        suffix = "" if self.using == "btree" else f"_{self.using}"
        base = f"crystaldba_idx_{self.table}_{column_part}_{len(self.columns)}"
        return f"{base}{suffix}"

    def __str__(self) -> str:
        return self.definition

    def __repr__(self) -> str:
        return f"IndexConfig(table='{self.table}', columns={self.columns}, using='{self.using}')"
