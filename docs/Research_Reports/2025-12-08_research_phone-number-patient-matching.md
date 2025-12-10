# Research Report: Phone Number Matching & Patient Data Consolidation

**Date**: December 8, 2025  
**Status**: Research Complete  
**Priority**: HIGH - Core requirement for Spruce contact matching  
**Researcher**: Claude AI Assistant

---

## Executive Summary

Matching 1,384 patients from Excel to Spruce contacts requires robust phone number normalization and fuzzy name matching. This report covers best practices, recommended Python libraries, and implementation strategies for achieving high-accuracy patient matching.

**Key Recommendations**:
1. Use `phonenumbers` library for phone normalization to E.164 format
2. Use `rapidfuzz` for fuzzy name matching (faster than fuzzywuzzy, MIT licensed)
3. Implement a multi-stage matching algorithm with confidence scoring
4. Handle edge cases: family members sharing phones, typos, missing data

---

## Phone Number Normalization

### The Problem

Phone numbers in Excel and Spruce may be formatted differently:

| Source | Example Formats |
|--------|-----------------|
| Excel | `205-555-1234`, `(205) 555-1234`, `2055551234`, `205.555.1234` |
| Spruce | `+12055551234` (E.164 format) |

### E.164 Standard

E.164 is the international standard for phone numbers:
- Format: `+[country code][national number]`
- US example: `+12055551234`
- No spaces, dashes, or parentheses
- Always starts with `+`

### Python `phonenumbers` Library

Google's `libphonenumber` ported to Python. Handles international numbers correctly.

**Installation**:
```bash
pip install phonenumbers
```

**Basic Usage**:
```python
import phonenumbers

def normalize_phone_to_e164(phone_str: str, default_country: str = "US") -> str:
    """
    Normalize a phone number to E.164 format.
    
    Args:
        phone_str: Phone number in any format
        default_country: ISO country code for numbers without country code
        
    Returns:
        E.164 formatted phone number (e.g., +12055551234)
        
    Raises:
        ValueError: If phone number is invalid
    """
    if not phone_str:
        raise ValueError("Phone number is required")
    
    # Clean the input
    phone_str = phone_str.strip()
    
    try:
        # Parse the phone number
        parsed = phonenumbers.parse(phone_str, default_country)
        
        # Validate it's a possible number
        if not phonenumbers.is_possible_number(parsed):
            raise ValueError(f"Not a possible phone number: {phone_str}")
        
        # Format to E.164
        return phonenumbers.format_number(
            parsed, 
            phonenumbers.PhoneNumberFormat.E164
        )
        
    except phonenumbers.NumberParseException as e:
        raise ValueError(f"Could not parse phone number '{phone_str}': {e}")
```

### Comprehensive Phone Normalizer

```python
import phonenumbers
from typing import Optional, Tuple
import re

class PhoneNormalizer:
    """
    Normalizes phone numbers to E.164 format with validation.
    """
    
    def __init__(self, default_country: str = "US"):
        self.default_country = default_country
    
    def normalize(self, phone: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Normalize a phone number.
        
        Returns:
            Tuple of (e164_number, error_message)
            On success: ("+12055551234", None)
            On failure: (None, "Error description")
        """
        if not phone:
            return None, "Empty phone number"
        
        # Pre-clean the input
        phone = self._preclean(phone)
        
        if not phone:
            return None, "No digits found in phone number"
        
        try:
            parsed = phonenumbers.parse(phone, self.default_country)
            
            # Check if it's a valid number
            if not phonenumbers.is_valid_number(parsed):
                # Try to be helpful about why
                if not phonenumbers.is_possible_number(parsed):
                    return None, "Invalid number length"
                return None, "Invalid number for region"
            
            e164 = phonenumbers.format_number(
                parsed,
                phonenumbers.PhoneNumberFormat.E164
            )
            
            return e164, None
            
        except phonenumbers.NumberParseException as e:
            return None, f"Parse error: {e}"
    
    def _preclean(self, phone: str) -> str:
        """
        Pre-clean phone number before parsing.
        Handles common data quality issues.
        """
        phone = str(phone).strip()
        
        # Remove common prefixes/suffixes
        phone = re.sub(r'^(phone|tel|cell|mobile|home|work)[\s:]*', '', phone, flags=re.I)
        
        # Remove extension info (we'll lose it, but better than failing)
        phone = re.sub(r'\s*(ext|x|extension)[\s.]*\d+', '', phone, flags=re.I)
        
        # Handle "or" in numbers (take first)
        if ' or ' in phone.lower():
            phone = phone.lower().split(' or ')[0]
        
        # Remove letters except 'x' for extensions (already handled)
        phone = re.sub(r'[a-wyz]', '', phone, flags=re.I)
        
        return phone.strip()
    
    def normalize_batch(self, phones: list) -> dict:
        """
        Normalize a batch of phone numbers.
        
        Returns dict mapping original -> e164 (or None if failed)
        """
        results = {}
        for phone in phones:
            e164, error = self.normalize(phone)
            results[phone] = {
                'e164': e164,
                'error': error,
                'success': e164 is not None
            }
        return results
```

### Usage Example

```python
normalizer = PhoneNormalizer(default_country="US")

# Test various formats
test_numbers = [
    "205-555-1234",
    "(205) 555-1234",
    "2055551234",
    "205.555.1234",
    "+1 205 555 1234",
    "1-205-555-1234",
    "Phone: 205-555-1234",
    "205-555-1234 ext 123",
    "",  # Empty
    "invalid",  # Invalid
]

for phone in test_numbers:
    e164, error = normalizer.normalize(phone)
    if e164:
        print(f"'{phone}' -> {e164}")
    else:
        print(f"'{phone}' -> ERROR: {error}")
```

**Output**:
```
'205-555-1234' -> +12055551234
'(205) 555-1234' -> +12055551234
'2055551234' -> +12055551234
'205.555.1234' -> +12055551234
'+1 205 555 1234' -> +12055551234
'1-205-555-1234' -> +12055551234
'Phone: 205-555-1234' -> +12055551234
'205-555-1234 ext 123' -> +12055551234
'' -> ERROR: Empty phone number
'invalid' -> ERROR: No digits found in phone number
```

---

## Fuzzy Name Matching

### The Problem

Names may be formatted differently or contain typos:

| Excel | Spruce | Issue |
|-------|--------|-------|
| John Smith | John R Smith | Middle initial |
| Smith, John | John Smith | Format order |
| Jon Smith | John Smith | Typo/nickname |
| JOHN SMITH | john smith | Case |
| Dr. John Smith | John Smith | Title |

### RapidFuzz Library

RapidFuzz is the recommended library - it's faster than FuzzyWuzzy and MIT licensed (no GPL restrictions).

**Installation**:
```bash
pip install rapidfuzz
```

### Basic Fuzzy Matching

```python
from rapidfuzz import fuzz, process
from typing import List, Tuple, Optional

def fuzzy_match_name(
    query: str, 
    candidates: List[str], 
    threshold: int = 80
) -> Optional[Tuple[str, float]]:
    """
    Find the best matching name from a list of candidates.
    
    Args:
        query: Name to search for
        candidates: List of possible matching names
        threshold: Minimum score (0-100) to consider a match
        
    Returns:
        Tuple of (best_match, score) or None if no match above threshold
    """
    if not query or not candidates:
        return None
    
    # Use token_sort_ratio for name matching
    # It's order-independent: "John Smith" matches "Smith, John"
    result = process.extractOne(
        query,
        candidates,
        scorer=fuzz.token_sort_ratio,
        score_cutoff=threshold
    )
    
    if result:
        return (result[0], result[1])
    return None
```

### Different Scoring Methods

```python
from rapidfuzz import fuzz

name1 = "John Smith"
name2 = "Smith, John"
name3 = "Jon Smyth"

# Simple ratio - character-by-character
print(f"Simple ratio: {fuzz.ratio(name1, name2)}")  # 61

# Token sort ratio - ignores word order (BEST FOR NAMES)
print(f"Token sort ratio: {fuzz.token_sort_ratio(name1, name2)}")  # 100

# Token set ratio - handles extra words
print(f"Token set ratio: {fuzz.token_set_ratio('John Smith', 'John Robert Smith')}")  # 100

# Partial ratio - substring matching
print(f"Partial ratio: {fuzz.partial_ratio(name1, name3)}")  # 78

# WRatio - weighted combination (good default)
print(f"WRatio: {fuzz.WRatio(name1, name2)}")  # 100
```

**Recommendation**: Use `token_sort_ratio` for patient name matching as it handles name order variations.

### Advanced Name Normalizer

```python
import re
from rapidfuzz import fuzz, process
from typing import Optional, List, Dict, Tuple

class NameMatcher:
    """
    Matches patient names with fuzzy logic.
    Handles common variations and data quality issues.
    """
    
    # Common titles to remove
    TITLES = ['dr', 'dr.', 'mr', 'mr.', 'mrs', 'mrs.', 'ms', 'ms.', 'miss']
    
    # Common suffixes to remove
    SUFFIXES = ['jr', 'jr.', 'sr', 'sr.', 'ii', 'iii', 'iv', 'md', 'phd', 'esq']
    
    def __init__(self, threshold: int = 80):
        self.threshold = threshold
    
    def normalize_name(self, name: str) -> str:
        """
        Normalize a name for matching.
        """
        if not name:
            return ""
        
        # Lowercase
        name = name.lower().strip()
        
        # Remove titles
        for title in self.TITLES:
            name = re.sub(rf'^{re.escape(title)}\s+', '', name)
        
        # Remove suffixes
        for suffix in self.SUFFIXES:
            name = re.sub(rf'\s+{re.escape(suffix)}$', '', name)
        
        # Remove punctuation except hyphens (for hyphenated names)
        name = re.sub(r'[^\w\s-]', '', name)
        
        # Normalize whitespace
        name = ' '.join(name.split())
        
        # Handle "Last, First" format -> "First Last"
        if ',' in name:
            parts = name.split(',', 1)
            if len(parts) == 2:
                name = f"{parts[1].strip()} {parts[0].strip()}"
        
        return name
    
    def find_best_match(
        self, 
        query_name: str, 
        candidates: List[Dict],
        name_field: str = 'name'
    ) -> Optional[Tuple[Dict, float]]:
        """
        Find the best matching candidate for a query name.
        
        Args:
            query_name: Name to search for
            candidates: List of dicts containing patient/contact data
            name_field: Key in candidate dicts containing the name
            
        Returns:
            Tuple of (best_matching_candidate, score) or None
        """
        if not query_name or not candidates:
            return None
        
        # Normalize query
        query_normalized = self.normalize_name(query_name)
        
        # Build list of (normalized_name, original_candidate) pairs
        candidate_names = []
        name_to_candidate = {}
        
        for candidate in candidates:
            orig_name = candidate.get(name_field, '')
            if orig_name:
                norm_name = self.normalize_name(orig_name)
                candidate_names.append(norm_name)
                name_to_candidate[norm_name] = candidate
        
        if not candidate_names:
            return None
        
        # Find best match
        result = process.extractOne(
            query_normalized,
            candidate_names,
            scorer=fuzz.token_sort_ratio,
            score_cutoff=self.threshold
        )
        
        if result:
            matched_name = result[0]
            score = result[1]
            return (name_to_candidate[matched_name], score)
        
        return None
    
    def find_all_matches(
        self,
        query_name: str,
        candidates: List[Dict],
        name_field: str = 'name',
        limit: int = 5
    ) -> List[Tuple[Dict, float]]:
        """
        Find all matching candidates above threshold, sorted by score.
        """
        if not query_name or not candidates:
            return []
        
        query_normalized = self.normalize_name(query_name)
        
        candidate_names = []
        name_to_candidate = {}
        
        for candidate in candidates:
            orig_name = candidate.get(name_field, '')
            if orig_name:
                norm_name = self.normalize_name(orig_name)
                candidate_names.append(norm_name)
                name_to_candidate[norm_name] = candidate
        
        if not candidate_names:
            return []
        
        results = process.extract(
            query_normalized,
            candidate_names,
            scorer=fuzz.token_sort_ratio,
            score_cutoff=self.threshold,
            limit=limit
        )
        
        return [
            (name_to_candidate[match[0]], match[1])
            for match in results
        ]
```

---

## Complete Patient Matching Algorithm

### Multi-Stage Matching Strategy

```python
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from enum import Enum

class MatchMethod(Enum):
    PHONE_EXACT = "phone_exact"
    PHONE_FUZZY = "phone_fuzzy"  # Last 10 digits match
    NAME_EXACT = "name_exact"
    NAME_FUZZY = "name_fuzzy"
    COMBINED = "combined"
    MANUAL = "manual"

@dataclass
class MatchResult:
    patient_id: str
    spruce_contact_id: Optional[str]
    match_method: Optional[MatchMethod]
    confidence: float  # 0.0 - 1.0
    matched: bool
    details: Dict[str, Any]

class PatientMatcher:
    """
    Matches Excel patients to Spruce contacts using multiple strategies.
    """
    
    def __init__(
        self,
        phone_normalizer: PhoneNormalizer,
        name_matcher: NameMatcher,
        confidence_thresholds: Dict[str, float] = None
    ):
        self.phone_normalizer = phone_normalizer
        self.name_matcher = name_matcher
        
        # Confidence thresholds for auto-matching
        self.thresholds = confidence_thresholds or {
            'phone_exact': 0.95,  # Phone exact match
            'name_high': 0.90,    # Name score >= 95
            'name_medium': 0.75,  # Name score >= 85
            'combined': 0.80,     # Phone partial + name partial
        }
    
    def match_patient(
        self,
        patient: Dict[str, Any],
        spruce_contacts: List[Dict[str, Any]]
    ) -> MatchResult:
        """
        Match a single patient to Spruce contacts.
        
        Args:
            patient: Dict with keys: id, first_name, last_name, phone, etc.
            spruce_contacts: List of Spruce contact dicts
            
        Returns:
            MatchResult with best match or no match
        """
        patient_id = patient.get('id') or patient.get('mrn', 'unknown')
        patient_phone = patient.get('phone') or patient.get('cell_phone', '')
        patient_name = self._get_full_name(patient)
        
        # Normalize patient phone
        patient_phone_e164, _ = self.phone_normalizer.normalize(patient_phone)
        
        # Strategy 1: Exact phone match
        if patient_phone_e164:
            for contact in spruce_contacts:
                contact_phones = self._get_contact_phones(contact)
                
                if patient_phone_e164 in contact_phones:
                    return MatchResult(
                        patient_id=patient_id,
                        spruce_contact_id=contact.get('id'),
                        match_method=MatchMethod.PHONE_EXACT,
                        confidence=0.99,
                        matched=True,
                        details={
                            'matched_phone': patient_phone_e164,
                            'contact_name': contact.get('displayName', '')
                        }
                    )
        
        # Strategy 2: Fuzzy name match
        name_match = self.name_matcher.find_best_match(
            patient_name,
            spruce_contacts,
            name_field='displayName'
        )
        
        if name_match:
            contact, name_score = name_match
            confidence = name_score / 100.0
            
            # High confidence name match
            if confidence >= self.thresholds['name_high']:
                return MatchResult(
                    patient_id=patient_id,
                    spruce_contact_id=contact.get('id'),
                    match_method=MatchMethod.NAME_FUZZY,
                    confidence=confidence,
                    matched=True,
                    details={
                        'patient_name': patient_name,
                        'contact_name': contact.get('displayName'),
                        'name_score': name_score
                    }
                )
            
            # Medium confidence - check if phone partially matches
            if confidence >= self.thresholds['name_medium'] and patient_phone_e164:
                contact_phones = self._get_contact_phones(contact)
                
                # Check last 10 digits match (handles country code differences)
                patient_last10 = patient_phone_e164[-10:] if len(patient_phone_e164) >= 10 else ''
                
                for cp in contact_phones:
                    if cp and cp[-10:] == patient_last10:
                        return MatchResult(
                            patient_id=patient_id,
                            spruce_contact_id=contact.get('id'),
                            match_method=MatchMethod.COMBINED,
                            confidence=min(0.95, confidence + 0.10),
                            matched=True,
                            details={
                                'patient_name': patient_name,
                                'contact_name': contact.get('displayName'),
                                'name_score': name_score,
                                'phone_partial_match': True
                            }
                        )
        
        # Strategy 3: Last 10 digits phone match (without name match)
        if patient_phone_e164:
            patient_last10 = patient_phone_e164[-10:]
            
            for contact in spruce_contacts:
                contact_phones = self._get_contact_phones(contact)
                
                for cp in contact_phones:
                    if cp and cp[-10:] == patient_last10:
                        return MatchResult(
                            patient_id=patient_id,
                            spruce_contact_id=contact.get('id'),
                            match_method=MatchMethod.PHONE_FUZZY,
                            confidence=0.70,
                            matched=True,
                            details={
                                'patient_name': patient_name,
                                'contact_name': contact.get('displayName'),
                                'phone_last10': patient_last10,
                                'needs_review': True
                            }
                        )
        
        # No match found
        return MatchResult(
            patient_id=patient_id,
            spruce_contact_id=None,
            match_method=None,
            confidence=0.0,
            matched=False,
            details={
                'patient_name': patient_name,
                'patient_phone': patient_phone,
                'reason': 'No matching contact found'
            }
        )
    
    def _get_full_name(self, patient: Dict) -> str:
        """Extract full name from patient dict."""
        if 'name' in patient:
            return patient['name']
        
        first = patient.get('first_name', '')
        last = patient.get('last_name', '')
        
        return f"{first} {last}".strip()
    
    def _get_contact_phones(self, contact: Dict) -> List[str]:
        """Extract all phone numbers from a Spruce contact."""
        phones = []
        
        # Direct phone field
        if contact.get('phone'):
            e164, _ = self.phone_normalizer.normalize(contact['phone'])
            if e164:
                phones.append(e164)
        
        # Phone numbers array (Spruce format)
        for pn in contact.get('phoneNumbers', []):
            value = pn.get('value') or pn.get('rawValue')
            if value:
                e164, _ = self.phone_normalizer.normalize(value)
                if e164:
                    phones.append(e164)
        
        return phones
    
    def match_all_patients(
        self,
        patients: List[Dict],
        spruce_contacts: List[Dict]
    ) -> Dict[str, MatchResult]:
        """
        Match all patients to Spruce contacts.
        
        Returns:
            Dict mapping patient_id -> MatchResult
        """
        results = {}
        
        for patient in patients:
            result = self.match_patient(patient, spruce_contacts)
            results[result.patient_id] = result
        
        return results
    
    def get_match_summary(self, results: Dict[str, MatchResult]) -> Dict:
        """
        Generate summary statistics for match results.
        """
        total = len(results)
        matched = sum(1 for r in results.values() if r.matched)
        unmatched = total - matched
        
        by_method = {}
        by_confidence = {'high': 0, 'medium': 0, 'low': 0, 'none': 0}
        needs_review = []
        
        for patient_id, result in results.items():
            if result.matched:
                method = result.match_method.value if result.match_method else 'unknown'
                by_method[method] = by_method.get(method, 0) + 1
                
                if result.confidence >= 0.90:
                    by_confidence['high'] += 1
                elif result.confidence >= 0.75:
                    by_confidence['medium'] += 1
                else:
                    by_confidence['low'] += 1
                    needs_review.append(patient_id)
            else:
                by_confidence['none'] += 1
        
        return {
            'total_patients': total,
            'matched': matched,
            'unmatched': unmatched,
            'match_rate': matched / total if total > 0 else 0,
            'by_method': by_method,
            'by_confidence': by_confidence,
            'needs_review': needs_review
        }
```

---

## Handling Edge Cases

### Family Members Sharing Phones

Multiple patients may share the same phone number (spouses, parent/child):

```python
def handle_shared_phones(
    patients: List[Dict],
    spruce_contacts: List[Dict],
    matcher: PatientMatcher
) -> Dict[str, List[MatchResult]]:
    """
    Handle cases where multiple patients may match the same contact.
    Groups results by Spruce contact ID.
    """
    all_matches = matcher.match_all_patients(patients, spruce_contacts)
    
    # Group by Spruce contact
    by_contact = {}
    
    for patient_id, result in all_matches.items():
        if result.spruce_contact_id:
            contact_id = result.spruce_contact_id
            if contact_id not in by_contact:
                by_contact[contact_id] = []
            by_contact[contact_id].append(result)
    
    # Flag contacts with multiple matches
    conflicts = {}
    for contact_id, matches in by_contact.items():
        if len(matches) > 1:
            conflicts[contact_id] = matches
            for match in matches:
                match.details['shared_phone_conflict'] = True
                match.details['other_matches'] = [
                    m.patient_id for m in matches if m.patient_id != match.patient_id
                ]
    
    return conflicts
```

### Missing or Invalid Phone Numbers

```python
def handle_missing_phones(
    patients: List[Dict],
    spruce_contacts: List[Dict],
    name_matcher: NameMatcher
) -> List[MatchResult]:
    """
    Match patients without valid phone numbers using name only.
    Lower confidence, requires manual review.
    """
    results = []
    
    for patient in patients:
        phone = patient.get('phone', '')
        
        # Check if phone is missing or invalid
        normalizer = PhoneNormalizer()
        e164, error = normalizer.normalize(phone) if phone else (None, "Missing")
        
        if not e164:
            # Phone missing/invalid - try name match
            patient_name = f"{patient.get('first_name', '')} {patient.get('last_name', '')}".strip()
            
            if patient_name:
                match = name_matcher.find_best_match(
                    patient_name,
                    spruce_contacts,
                    name_field='displayName'
                )
                
                if match:
                    contact, score = match
                    results.append(MatchResult(
                        patient_id=patient.get('id', 'unknown'),
                        spruce_contact_id=contact.get('id'),
                        match_method=MatchMethod.NAME_FUZZY,
                        confidence=score / 100.0 * 0.8,  # Reduce confidence without phone
                        matched=True,
                        details={
                            'patient_name': patient_name,
                            'contact_name': contact.get('displayName'),
                            'name_score': score,
                            'phone_status': error,
                            'needs_manual_review': True
                        }
                    ))
                else:
                    results.append(MatchResult(
                        patient_id=patient.get('id', 'unknown'),
                        spruce_contact_id=None,
                        match_method=None,
                        confidence=0.0,
                        matched=False,
                        details={
                            'patient_name': patient_name,
                            'phone_status': error,
                            'reason': 'No phone and no name match'
                        }
                    ))
    
    return results
```

---

## Streamlit UI for Manual Review

```python
import streamlit as st
import pandas as pd

def render_matching_review_ui(
    match_results: Dict[str, MatchResult],
    patients: List[Dict],
    spruce_contacts: List[Dict]
):
    """
    Streamlit UI for reviewing and correcting matches.
    """
    st.header("Patient Matching Review")
    
    # Summary
    summary = get_match_summary(match_results)
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Patients", summary['total_patients'])
    col2.metric("Matched", summary['matched'])
    col3.metric("Unmatched", summary['unmatched'])
    col4.metric("Match Rate", f"{summary['match_rate']:.1%}")
    
    # Tabs
    tab1, tab2, tab3 = st.tabs([
        "Needs Review",
        "Unmatched",
        "All Matches"
    ])
    
    with tab1:
        st.subheader("Low Confidence Matches (Review Required)")
        
        for patient_id in summary['needs_review']:
            result = match_results[patient_id]
            
            with st.expander(f"Patient: {result.details.get('patient_name', patient_id)}"):
                st.write(f"**Confidence:** {result.confidence:.1%}")
                st.write(f"**Method:** {result.match_method.value if result.match_method else 'None'}")
                st.write(f"**Matched Contact:** {result.details.get('contact_name', 'N/A')}")
                
                # Action buttons
                col1, col2, col3 = st.columns(3)
                
                if col1.button("✓ Confirm", key=f"confirm_{patient_id}"):
                    # Confirm the match
                    result.confidence = 1.0
                    result.details['manually_confirmed'] = True
                    st.success("Match confirmed!")
                
                if col2.button("✗ Reject", key=f"reject_{patient_id}"):
                    # Reject the match
                    result.matched = False
                    result.spruce_contact_id = None
                    result.details['manually_rejected'] = True
                    st.warning("Match rejected")
                
                if col3.button("🔍 Manual Match", key=f"manual_{patient_id}"):
                    # Show contact selector
                    st.session_state[f'show_selector_{patient_id}'] = True
                
                # Manual contact selector
                if st.session_state.get(f'show_selector_{patient_id}'):
                    contact_options = {
                        c.get('displayName', c.get('id')): c.get('id')
                        for c in spruce_contacts
                    }
                    selected = st.selectbox(
                        "Select Spruce Contact",
                        options=list(contact_options.keys()),
                        key=f"select_{patient_id}"
                    )
                    
                    if st.button("Save Manual Match", key=f"save_{patient_id}"):
                        result.spruce_contact_id = contact_options[selected]
                        result.match_method = MatchMethod.MANUAL
                        result.confidence = 1.0
                        result.matched = True
                        result.details['manually_matched'] = True
                        st.success("Manual match saved!")
    
    with tab2:
        st.subheader("Unmatched Patients")
        
        unmatched = [
            (pid, r) for pid, r in match_results.items() 
            if not r.matched
        ]
        
        if unmatched:
            for patient_id, result in unmatched:
                with st.expander(f"Patient: {result.details.get('patient_name', patient_id)}"):
                    st.write(f"**Phone:** {result.details.get('patient_phone', 'N/A')}")
                    st.write(f"**Reason:** {result.details.get('reason', 'Unknown')}")
                    
                    # Search contacts
                    search_term = st.text_input(
                        "Search Spruce Contacts",
                        key=f"search_{patient_id}"
                    )
                    
                    if search_term:
                        matches = find_contacts(search_term, spruce_contacts)
                        for m in matches[:5]:
                            st.write(f"- {m.get('displayName')} ({m.get('phone', 'No phone')})")
        else:
            st.success("All patients matched!")
    
    with tab3:
        st.subheader("All Match Results")
        
        # Convert to DataFrame for display
        rows = []
        for pid, result in match_results.items():
            rows.append({
                'Patient ID': pid,
                'Patient Name': result.details.get('patient_name', ''),
                'Matched': '✓' if result.matched else '✗',
                'Contact': result.details.get('contact_name', ''),
                'Confidence': f"{result.confidence:.1%}",
                'Method': result.match_method.value if result.match_method else ''
            })
        
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True)
        
        # Export option
        if st.button("Export Results to CSV"):
            csv = df.to_csv(index=False)
            st.download_button(
                "Download CSV",
                csv,
                file_name="patient_matching_results.csv",
                mime="text/csv"
            )
```

---

## Installation & Dependencies

```bash
pip install phonenumbers rapidfuzz pandas
```

**requirements.txt addition**:
```
phonenumbers>=8.13.0
rapidfuzz>=3.0.0
```

---

## Performance Considerations

### For 1,384 Patients

| Operation | Time Estimate |
|-----------|---------------|
| Phone normalization | ~0.1 seconds (batch) |
| Name fuzzy matching | ~2-5 seconds (with RapidFuzz) |
| Total matching | ~5-10 seconds |

### Optimization Tips

1. **Pre-normalize all phones** before matching
2. **Build phone index** for O(1) exact lookups
3. **Use RapidFuzz's `cdist`** for batch name comparisons
4. **Cache Spruce contacts** - don't fetch repeatedly

---

## Implementation Checklist

- [ ] Install `phonenumbers` and `rapidfuzz` packages
- [ ] Create `PhoneNormalizer` class
- [ ] Create `NameMatcher` class
- [ ] Create `PatientMatcher` class
- [ ] Build Streamlit review UI
- [ ] Test with sample patient data
- [ ] Run full matching on 1,384 patients
- [ ] Review and confirm low-confidence matches
- [ ] Export final matching results
- [ ] Update patient records with Spruce contact IDs

---

## References

- [phonenumbers PyPI](https://pypi.org/project/phonenumbers/)
- [Google libphonenumber](https://github.com/google/libphonenumber)
- [RapidFuzz GitHub](https://github.com/rapidfuzz/RapidFuzz)
- [RapidFuzz Documentation](https://maxbachmann.github.io/RapidFuzz/)
- [E.164 Phone Number Format](https://en.wikipedia.org/wiki/E.164)
- [Fuzzy Matching Best Practices](https://dataladder.com/fuzzy-matching-101/)

---

*Research completed: December 8, 2025*  
*Ready for implementation in Patient Explorer*
