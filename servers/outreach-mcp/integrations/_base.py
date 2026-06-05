"""Shared provider primitives. One CreditError so the enrichment chain can catch
exhaustion by type (not by fragile class-name string matching)."""


class CreditError(Exception):
    """A provider signalled credit exhaustion (HTTP 402/403/429 on a billable op)."""
