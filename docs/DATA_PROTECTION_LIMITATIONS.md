# FinGuard AI: Inbound Data Protection Limitations & Detection Boundaries

**Document Version**: 1.0.0  
**Domain**: Inbound Data Classification & Sensitive Candidate Detection  

---

## 1. Core Detection Philosophy & Candidate Disclaimer

> [!IMPORTANT]
> **SYNTHETIC & CANDIDATE DISCLAIMER**
> 1. **No Proof of Live Entity Existence**: Passing a Luhn (credit card) or Verhoeff (Aadhaar) checksum algorithm check indicates that a number string satisfies the *mathematical format specification* of a candidate entity. It **never proves that an actual live credit card, active bank account, or registered Aadhaar identity exists**.
> 2. **Zero-Raw Secret Persistence**: FinGuard AI audit traces and telemetry streams **NEVER log or record raw unmasked sensitive candidate strings**. Audit trace records contain only safe masked placeholders, positional index offsets, and checksum flags.
> 3. **Synthetic Test Data Mandate**: Testing and sandbox validation must utilize synthetic test vectors only (e.g. standard Luhn-valid test card numbers `4532-XXXX-XXXX-9981` or synthetic Verhoeff test strings).

---

## 2. Documented Limitations & Likely False Positives

Deterministic pattern matching and checksum algorithms provide ultra-fast ($< 1\text{ ms}$) structural detection boundaries, but exhibit known edge-case limitations:

| Candidate Type | Detection Method & Checksum | Likely False Positive Scenarios | Mitigation in FinGuard AI |
| :--- | :--- | :--- | :--- |
| **Payment Card** | 13–19 digit regex + **Luhn Checksum** (Mod 10). | 16-digit tracking numbers, inventory serials, or product IDs that accidentally satisfy Luhn checksum. | Requires 13–19 digit format bounds; format-preserving mask retains first 4 / last 4 digits (`[RED_CARD_4532-XXXX-XXXX-9981]`). |
| **Aadhaar Identity** | 12-digit regex + **Verhoeff Checksum**. | 12-digit invoice numbers, transaction reference codes, or meter readings starting with digits 2–9. | Excludes numbers starting with `0` or `1`; Verhoeff check digit validation reduces false positives by $> 90\%$. |
| **PAN (Permanent Account Number)** | 10-char regex `[A-Z]{5}[0-9]{4}[A-Z]{1}`. | Random 10-character code strings (e.g. coupon codes, Git commit IDs) matching 5-letter/4-digit/1-letter structure. | Validates 4th character entity type classifier (`P`, `C`, `H`, `F`, `A`, `T`, `B`, `L`, `J`, `G`). |
| **Bank Account Number** | 9–18 digit regex + Context Keywords. | Order IDs or timestamps appearing immediately after generic words like "account". | Requires explicit preceding context keywords (`account #`, `acct`, `a/c`, `acc no`); preserves last 4 digits. |
| **OTP / Passcode** | 4–8 digit regex + Context Keywords. | Monetary amounts or year numbers appearing near words like "code" or "pin". | Requires proximity keywords (`otp`, `passcode`, `verification code`, `auth code`); masks full code (`[RED_OTP_****]`). |

---

## 3. Preserving Context Utility for LLM Prompts

FinGuard AI balances security protection with LLM prompt usefulness. Rather than stripping entire sentences, the engine uses **format-preserving placeholders**:

- *Original User Query*:  
  `"Please transfer $500 from my checking account 9876543210 to Aadhaar 2345 6789 0123 for OTP 4921."`
- *Transformed Prompt (Passed to LLM)*:  
  `"Please transfer $500 from my checking account [RED_ACCT_...3210] to Aadhaar [RED_AADHAAR_XXXX-XXXX-0123] for OTP [RED_OTP_****]."`

The LLM receives full semantic structure ("transfer $500 from account X to Aadhaar Y for OTP Z") without ever being exposed to raw account numbers, identity numbers, or one-time passcodes.

---

## 4. Synthetic Test Value Reference Guide

For automated testing, developer sandboxes, and CI/CD pipelines, use these synthetic test vectors:

- **Synthetic Luhn-Valid Credit Card**: `4532 0123 8594 9981`
- **Synthetic Luhn-Invalid Credit Card**: `4532 0123 8594 9982` (Fails Luhn check)
- **Synthetic Verhoeff-Valid Aadhaar**: `2345 6789 0123` (Calculated Verhoeff check digit)
- **Synthetic PAN**: `ABCDE1234F` (Individual status `P` in 4th character)
- **Synthetic Email**: `alice.test@bankdomain.com`
- **Synthetic Phone**: `800-555-0199`
