# FinGuard AI: Secure Pre-Context Retrieval-Augmented Generation (RAG)

**Document Version**: 1.0.0  
**Domain**: Pre-Context Security Filtering, Cross-Customer Isolation, & Indirect Prompt Injection Scanning  

---

## 1. Architectural Architecture & Pre-Context Filtering

FinGuard AI enforces **pre-context security filtering** on all retrieved documents prior to constructing the LLM prompt context. Access control decisions are evaluated deterministically in the gateway—**never relying on the LLM to decide whether a requester is authorized**.

```
[ User Query + Identity ] ----> [ Candidate Retrieval ] ----> [ Secure RAG Guard ] ----> [ Safe LLM Context ]
                                                                      |
                                                  +-------------------+-------------------+
                                                  |                   |                   |
                                           [ Metadata Check ]  [ Role Authorization ]  [ Cross-Customer Isolation ]
                                           [ Fail-Safe Deny ]  [ Indirect Injection ]  [ Encapsulated XML Context ]
```

---

## 2. Document Metadata Schema & Classification Tiers

Every synthetic or production RAG document must contain mandatory permission metadata:

| Field | Type | Description |
| :--- | :--- | :--- |
| `doc_id` | `str` | Unique document identifier (e.g. `DOC-FAQ-001`) |
| `title` | `str` | Document title |
| `classification` | `Enum` | `PUBLIC`, `INTERNAL`, `RESTRICTED_CUSTOMER`, or `CONFIDENTIAL` |
| `owner_id` | `Optional[str]` | Customer owner ID (e.g. `USR-1001`) for customer-restricted records |
| `permitted_roles` | `List[str]` | List of authorized user roles (e.g. `["RetailCustomer", "WealthManager"]`) |
| `version` | `str` | Corpus metadata version string |

---

## 3. Pre-Context Security Rules

1. **Metadata Validation & Fail-Safe Denial**: If permission metadata is missing (`classification=None`) or `permitted_roles` is empty, access is **denied safely** (`DENIED_INVALID_METADATA`).
2. **Public vs. Restricted Separation**: Public banking FAQs (`PUBLIC`) are accessible across allowed roles, while restricted customer documents (`RESTRICTED_CUSTOMER`) require strict owner matching.
3. **Cross-Customer Isolation**: A user (`USR-1001`) can **never** retrieve another user's (`USR-1002`) documents (`DENIED_OWNER`).
4. **Untrusted Text & Indirect Injection Scan**: All document contents are treated as untrusted data. Retrieved documents containing embedded malicious instructions (`SYSTEM OVERRIDE`, `Ignore previous instructions`, exfiltration requests) are quarantined and excluded from context (`POISONING_BLOCKED`).
5. **XML Delimiter Encapsulation**: Authorized documents are wrapped in boundary-enforced XML blocks (`<retrieved_reference_documents>`), clearly framing the text as untrusted reference data for the model.
6. **Zero-Data-Leakage Audit Logging**: Audit logs record document IDs, titles, classifications, access decisions, and reason codes without logging raw confidential text.

---

## 4. Important Security Disclaimer & Limitations

> [!CAUTION]
> **PROMPT INJECTION PREVENTION DISCLAIMER**  
> Access-control and pre-context filtering tests validate role authorization, metadata completeness, customer data isolation, and known indirect injection pattern detection. **However, access-control tests do NOT prove complete prompt-injection prevention.** Complex, novel, or adversarial multi-turn indirect prompt injections in retrieved context may bypass heuristic pattern matchers. Defense-in-depth measures (including output validation and tool action firewalls) must be maintained across all gateway tiers.
