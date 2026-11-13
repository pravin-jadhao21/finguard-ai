# FinGuard AI Security Policy Directory

This directory contains declarative YAML policy configurations defining rule weights, sanitization rules, and threshold boundaries for the gateway.

## Policy Schema Structure
- `policy.version`: Semantic version string of the active rule set.
- `policy.sanitization`: Inbound string processing rules (NFKC normalization, max bytes).
- `policy.pii_pci_redaction`: Rule toggles and format-preserving masking parameters.
- `policy.rules`: List of rule IDs, descriptions, categories, actions (`MASK`, `DENY`, `ALLOW`), and weights.
