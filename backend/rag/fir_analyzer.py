"""
FIR (First Information Report) Analyzer Module
---------------------------------------------
Analyzes FIR narratives or text under Indian Law:
- Maps alleged facts to Bharatiya Nyaya Sanhita (BNS) offenses.
- Classifies arrest powers & bail status under Bharatiya Nagarik Suraksha Sanhita (BNSS).
- Explains citizen legal rights & next procedural steps.
- Strictly adheres to the rule: legal information, not legal advice.
"""

import re
from typing import Any, Dict, List, Optional
from backend.config import LEGAL_DISCLAIMER
from backend.rag.vector_store import get_vector_store

# Sample FIR templates for fast testing and college viva demonstration
SAMPLE_FIRS = {
    "cyber_fraud": {
        "title": "Cyber Phishing & Financial Fraud (Cheating)",
        "police_station": "Cyber Crime Police Station, Bengaluru East",
        "date": "15 Jan 2026",
        "text": (
            "To the Station House Officer, Cyber Crime PS. "
            "I, Rahul Sharma, state that on 14 Jan 2026, I received a call from an unknown person "
            "posing as a bank executive from SBI. The caller deceived me into believing that my debit card "
            "was blocked and fraudulently induced me to share my OTP. Immediately thereafter, an unauthorized "
            "transaction of Rs 45,000 was debited from my account. When I asked for a refund, the accused "
            "dishonestly misappropriated the amount and switched off their phone. "
            "I request registration of an FIR for cheating, online fraud, and dishonest inducement."
        )
    },
    "theft": {
        "title": "Motorcycle Theft from Parking Area",
        "police_station": "Indiranagar Police Station",
        "date": "18 Jan 2026",
        "text": (
            "To the Inspector of Police. "
            "I, Priya Verma, parked my Honda Activa (Registration KA-03-HF-9821) at the Metro Station "
            "parking lot on 17 Jan 2026 at 9:00 AM. When I returned in the evening at 6:30 PM, the vehicle "
            "was missing. I checked with the security guard and confirmed that an unidentified person moved "
            "and took away my two-wheeler dishonestly without my consent. "
            "I request you to register an FIR for vehicle theft and recover my stolen property."
        )
    },
    "assault_hurt": {
        "title": "Physical Assault and Intimidation",
        "police_station": "Civil Lines Police Station",
        "date": "20 Jan 2026",
        "text": (
            "To the Station House Officer. "
            "On 19 Jan 2026 around 8:00 PM, while returning from the market, my neighbor Mr. Rakesh Verma "
            "stopped me over a parking dispute. He made threatening gestures, used abusive language, "
            "and used criminal force to push me against a wall. He intentionally caused bodily pain and "
            "hurt to my right arm and threatened to harm me further if I complained. "
            "Kindly register an FIR for assault, voluntarily causing hurt, and criminal intimidation."
        )
    }
}


def extract_fir_entities(text: str) -> Dict[str, Any]:
    """
    Extracts key metadata from FIR text like monetary loss, vehicle numbers, dates.
    """
    entities = {}

    # Check for monetary amounts (e.g. Rs 45,000 or INR 50000)
    money_match = re.search(r"(?:Rs\.?|INR|₹)\s?([0-9,]+)", text, re.IGNORECASE)
    if money_match:
        entities["financial_loss"] = f"Rs. {money_match.group(1)}"

    # Check for vehicle registration pattern (e.g. KA-03-HF-9821, DL-01-AB-1234)
    vehicle_match = re.search(r"\b([A-Z]{2}[-\s]?[0-9]{1,2}[-\s]?[A-Z]{1,3}[-\s]?[0-9]{4})\b", text)
    if vehicle_match:
        entities["vehicle_number"] = vehicle_match.group(1)

    # Check for date pattern
    date_match = re.search(r"\b(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})\b", text, re.IGNORECASE)
    if date_match:
        entities["incident_date"] = date_match.group(1)

    return entities


def analyze_fir_text(fir_text: str) -> Dict[str, Any]:
    """
    Analyzes an FIR narrative and returns structured legal findings:
    - Matched BNS offense sections.
    - Procedural classification (Cognizable/Non-Cognizable, Bailable/Non-Bailable).
    - Arrest & bail guidance under BNSS.
    - Next steps & citizen rights.
    """
    clean_text = fir_text.strip()
    if not clean_text:
        return {
            "error": "FIR text cannot be empty.",
            "disclaimer": LEGAL_DISCLAIMER
        }

    # 1. Extract metadata entities
    entities = extract_fir_entities(clean_text)

    # 2. Query Knowledge Base for matching substantive offenses (BNS)
    vector_store = get_vector_store()
    matched_provisions = vector_store.search(
        query=clean_text,
        n_results=3,
        act_filter="BNS"
    )

    # If no BNS sections matched, perform a broader search
    if not matched_provisions:
        matched_provisions = vector_store.search(query=clean_text, n_results=2)

    # 3. Analyze bail and arrest classification
    is_cognizable = False
    is_non_bailable = False
    sections_summary = []

    for p in matched_provisions:
        cognizable_str = p.get("cognizable", "")
        bailable_str = p.get("bailable", "")

        if "cognizable" in cognizable_str.lower() and "non-cognizable" not in cognizable_str.lower():
            is_cognizable = True
        if "non-bailable" in bailable_str.lower():
            is_non_bailable = True

        sections_summary.append({
            "act": p.get("act_short", "BNS"),
            "section": p.get("section"),
            "title": p.get("title"),
            "punishment": p.get("punishment"),
            "cognizable": cognizable_str,
            "bailable": bailable_str,
            "description": p.get("description")
        })

    # Overall Case Classification
    overall_nature = "Cognizable Offense" if is_cognizable else "Non-Cognizable Offense"
    overall_bail = "Non-Bailable" if is_non_bailable else "Bailable"

    # 4. Generate Procedural Guidance under BNSS
    arrest_guidance = (
        "Under Section 35 of BNSS (2023), police have the power to arrest without a warrant "
        "if credible information indicates commission of a cognizable offense. However, for offenses "
        "punishable with up to 7 years imprisonment, police must first issue a Notice of Appearance "
        "unless immediate arrest is justified in writing."
        if is_cognizable else
        "Under Section 35 of BNSS, police cannot arrest without a warrant for a non-cognizable offense. "
        "The matter must be investigated upon permission or summons from the Judicial Magistrate."
    )

    bail_guidance = (
        "Since one or more alleged offenses are Non-Bailable, bail cannot be claimed as a matter "
        "of right at the police station. The accused person must apply for regular bail before the "
        "Judicial Magistrate / Sessions Court under Section 479 of BNSS, or apply for Anticipatory "
        "Bail under Section 482 of BNSS if arrest is apprehended."
        if is_non_bailable else
        "The alleged offenses are classified as Bailable. Bail can be granted as a matter of right "
        "upon furnishing a personal bond or solvent surety before the Station House Officer (SHO) "
        "or the Magistrate."
    )

    # 5. Citizen Rights & Action Checklist
    action_steps = [
        "Right to Free Copy: Under BNSS Section 173(2), an informant is legally entitled to receive a free copy of the FIR immediately upon registration.",
        "Refusal Remedy: If a police station refuses to register an FIR for a cognizable crime, you may send the substance in writing by registered post to the Superintendent of Police (SP) under BNSS Section 173(3).",
        "Evidence Preservation: Preserve all digital messages, call records, CCTV clips, or receipts. Under Section 63 of Bharatiya Sakshya Adhiniyam (BSA), a certificate is required to prove electronic records in court.",
        "Legal Assistance: If you cannot afford an advocate, you have a statutory right to free legal aid through your District Legal Services Authority (DLSA)."
    ]

    return {
        "status": "success",
        "fir_length_chars": len(clean_text),
        "entities_detected": entities,
        "overall_classification": {
            "nature": overall_nature,
            "bail_status": overall_bail,
            "is_cognizable": is_cognizable,
            "is_non_bailable": is_non_bailable
        },
        "matched_sections": sections_summary,
        "arrest_power_guidance": arrest_guidance,
        "bail_guidance": bail_guidance,
        "citizen_rights_and_steps": action_steps,
        "disclaimer": LEGAL_DISCLAIMER
    }
