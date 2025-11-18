# TrustLens Badge Logic Update - Complete Documentation

## Summary of Changes

This document describes all the updates made to the TrustLens badge hover logic, evidence analysis, and toxicity detection system.

---

## 1. Updated Badge Hover Labels

### Tone Labels (Based on Toxicity)
- **Red (Toxic - score ≥ 0.5)** → `"Strong language"`
- **Yellow (Mild - score 0.3-0.5)** → `"Slightly strong language"`
- **Green (Neutral - score < 0.3)** → `"Positive tone"`

### Evidence Labels (Based on Evidence Status)
- **Verified** → `"Verifiable evidence present"`
- **Unverified** → `"Unverifiable evidence"`
- **Mixed** → `"Partially verifiable evidence"`
- **None** → `"No evidence"`
- **Evidence present, unverified** → `"Unverifiable evidence"`

### Source Labels (Based on URL Presence and Verification)
- **Verified URL present** → Shows the actual verified URL (e.g., `"https://www.cdc.gov/"`)
- **Unverified URL present** → `"URL is not verified"`
- **No URL** → `"URL is not present"`

---

## 2. Files Modified

### Frontend Changes

#### `chrome-extension/trustlens-badges.js`

**Lines 848-937: Updated `getPopupContent()` method**
- Added helper functions to determine labels dynamically:
  - `getToneLabel(toxicityColor, fallbackBadgeColor)` - Maps colors to tone labels
  - `getEvidenceLabel(status)` - Maps evidence status to labels
  - `getSourceLabel(status, evidence)` - Determines source label based on URL verification
- Popup now uses `toxicity_color` from API response for accurate tone detection
- Source label shows actual verified URLs when available

**Lines 1132-1139: Updated badge data storage**
- Added `toxicity_color` to `badgeData` object to pass toxicity information to popup

### Backend Changes

#### `api/evidence.py`

**Lines 350-387: Updated TL2/TL3 tooltip generation**
- **Verified status**:
  - TL2: "Verifiable evidence present"
  - TL3: Shows up to 3 verified URLs
- **Mixed status**:
  - TL2: "Partially verifiable evidence"
  - TL3: Shows count and samples of verified/unverified domains
- **Unverified status**:
  - TL2: "Unverifiable evidence"
  - TL3: "URL is not verified" with sample URLs
- **None status**:
  - TL2: "No evidence"
  - TL3: "URL is not present"

#### `api/main.py`

**Lines 198-233: Badge color determination logic**
```python
def determine_badge_color(toxicity_color: str, evidence_status: str) -> str:
    if toxicity_color == "red":
        return "red"  # Toxic always red
    elif toxicity_color == "yellow":
        return "yellow"  # Mild always yellow
    else:  # green (Neutral)
        if evidence_status in ["Verified", "None"]:
            return "green"
        else:  # Unverified/Mixed
            return "yellow"
```

**Lines 235-322: analyze-evidence endpoint**
- Returns `toxicity_color` in response for frontend use
- Includes detailed toxicity scores and evidence results

#### `api/toxicity_model/app.py`

**Lines 42-58: Toxicity threshold logic (Verified as correct)**
```python
def _badge_color_for_row(row_probs: np.ndarray) -> str:
    toxic_score = float(row_probs[0])
    if toxic_score >= 0.5:
        return "red"
    elif toxic_score >= 0.3:
        return "yellow"
    else:
        return "green"
```

---

## 3. Complete Logic Flow

### Step 1: Comment Analysis
1. User hovers over a Reddit comment
2. Frontend extracts comment text
3. Sends to `/analyze-evidence` endpoint

### Step 2: Backend Processing
1. **Toxicity Analysis** (via toxicity model):
   - Calculates toxic score (0-1)
   - Maps to color:
     - ≥ 0.5 → Red (Toxic)
     - 0.3-0.5 → Yellow (Mild)
     - < 0.3 → Green (Neutral)

2. **Evidence Analysis** (via evidence.py):
   - Extracts URLs from text
   - Verifies each URL (DNS, HTTP, content type)
   - Determines status:
     - All verified → "Verified"
     - Some verified → "Mixed"
     - None verified but URLs present → "Unverified"
     - No URLs but evidence patterns → "Evidence present, unverified"
     - No URLs, no patterns → "None"

3. **Badge Color Determination**:
   - Combines toxicity + evidence per TL1 spec
   - Returns final badge color

### Step 3: Frontend Display
1. Receives response with:
   - `badge_color` (red/yellow/green)
   - `toxicity_color` (red/yellow/green)
   - `status` (Verified/Unverified/Mixed/None/Evidence present, unverified)
   - `evidence` (detailed URL verification results)

2. Creates popup with three sections:
   - **Tone**: Determined from `toxicity_color`
   - **Evidence**: Determined from `status`
   - **Source**: Shows URL if verified, otherwise status message

---

## 4. All Possible Scenarios (20 Test Cases)

### Scenario Matrix

| ID | Toxicity | Evidence | URLs | Badge Color | Tone Label | Evidence Label | Source Label |
|----|----------|----------|------|-------------|------------|----------------|--------------|
| 1 | Green | Verified | Yes | Green | Positive tone | Verifiable evidence present | [URL shown] |
| 2 | Green | None | No | Green | Positive tone | No evidence | URL is not present |
| 3 | Green | Unverified | Yes | Yellow | Positive tone | Unverifiable evidence | URL is not verified |
| 4 | Green | Mixed | Yes | Yellow | Positive tone | Partially verifiable evidence | [Mix of verified/not] |
| 5 | Yellow | Verified | Yes | Yellow | Slightly strong language | Verifiable evidence present | [URL shown] |
| 6 | Yellow | None | No | Yellow | Slightly strong language | No evidence | URL is not present |
| 7 | Yellow | Unverified | Yes | Yellow | Slightly strong language | Unverifiable evidence | URL is not verified |
| 8 | Red | Verified | Yes | Red | Strong language | Verifiable evidence present | [URL shown] |
| 9 | Red | None | No | Red | Strong language | No evidence | URL is not present |
| 10 | Red | Unverified | Yes | Red | Strong language | Unverifiable evidence | URL is not verified |
| 11 | Green | Evidence present | No | Yellow | Positive tone | Unverifiable evidence | URL is not present |
| 12 | Green | Verified | Yes (Multiple) | Green | Positive tone | Verifiable evidence present | [URLs shown] |
| 13 | Yellow | Mixed | Yes | Yellow | Slightly strong language | Partially verifiable evidence | [Mix of verified/not] |
| 14 | Red | Mixed | Yes | Red | Strong language | Partially verifiable evidence | [Mix of verified/not] |
| 15 | Yellow (~0.3) | None | No | Yellow | Slightly strong language | No evidence | URL is not present |
| 16 | Red (~0.5) | None | No | Red | Strong language | No evidence | URL is not present |
| 17 | Green | Verified | Yes (.gov) | Green | Positive tone | Verifiable evidence present | [.gov URL] |
| 18 | Green | Verified | Yes (.edu) | Green | Positive tone | Verifiable evidence present | [.edu URL] |
| 19 | Green | Unverified | Yes (localhost) | Yellow | Positive tone | Unverifiable evidence | URL is not verified |
| 20 | Green | Verified | Yes (PDF) | Green | Positive tone | Verifiable evidence present | [PDF URL] |

---

## 5. Testing Instructions

### Prerequisites
1. Start the API server:
   ```bash
   cd api
   uvicorn main:app --reload --port 8000
   ```

2. Load the Chrome extension in developer mode

### Running Tests

#### Automated Testing
```bash
python test_badge_logic.py
```

This will:
- Test all 20 scenarios from `test_sample_data.json`
- Generate detailed results
- Save results to `test_results.json`

#### Manual Testing
1. Navigate to a Reddit post
2. Observe badge colors on comments
3. Hover over badges to see popup
4. Verify:
   - Tone label matches comment toxicity
   - Evidence label matches source verification
   - Source label shows URL or appropriate message

---

## 6. Example Outputs

### Example 1: Neutral + Verified URL
**Comment**: "According to NASA https://climate.nasa.gov/, temperatures are rising."

**Popup Display**:
```
Content analysis complete
─────────────────────────
Tone: Positive tone
Evidence: Verifiable evidence present
Source: https://climate.nasa.gov/
```

### Example 2: Toxic + No URL
**Comment**: "You're an idiot and don't know anything!"

**Popup Display**:
```
Content analysis complete
─────────────────────────
Tone: Strong language
Evidence: No evidence
Source: URL is not present
```

### Example 3: Neutral + Unverified URL
**Comment**: "Check this out http://fake-news-123.com/article"

**Popup Display**:
```
Content analysis complete
─────────────────────────
Tone: Positive tone
Evidence: Unverifiable evidence
Source: URL is not verified
```

### Example 4: Mild + Mixed URLs
**Comment**: "This is questionable. See https://www.who.int/ and http://random-blog.fake/"

**Popup Display**:
```
Content analysis complete
─────────────────────────
Tone: Slightly strong language
Evidence: Partially verifiable evidence
Source: https://www.who.int/ (first verified URL)
```

---

## 7. Badge Color Logic Table

| Toxicity Color | Evidence Status | Final Badge Color | Reasoning |
|----------------|-----------------|-------------------|-----------|
| Red | Any | **Red** | Toxic content overrides evidence |
| Yellow | Any | **Yellow** | Mild toxicity overrides evidence |
| Green | Verified | **Green** | Neutral + verified sources |
| Green | None | **Green** | Neutral opinion, no evidence needed |
| Green | Unverified | **Yellow** | Neutral but unverified claims |
| Green | Mixed | **Yellow** | Neutral but partially unverified |
| Green | Evidence present, unverified | **Yellow** | Neutral but unverifiable claims |

---

## 8. API Response Format

### `/analyze-evidence` Response
```json
{
  "status": "Verified",
  "badge_color": "green",
  "toxicity_color": "green",
  "toxicity_scores": {
    "toxic": 0.12,
    "severe_toxic": 0.01,
    "obscene": 0.02,
    "threat": 0.00,
    "insult": 0.05,
    "identity_hate": 0.01
  },
  "evidence": {
    "comment_id": "comment_abc123",
    "text": "According to NASA...",
    "urls": ["https://climate.nasa.gov/"],
    "status": "Verified",
    "results": [{
      "input_url": "https://climate.nasa.gov/",
      "normalized_url": "https://climate.nasa.gov/",
      "final_url": "https://climate.nasa.gov/",
      "domain": "climate.nasa.gov",
      "verified": true,
      "category": "government",
      "confidence": 0.9
    }]
  },
  "TL2_tooltip": "Verifiable evidence present",
  "TL3_detail": "Verified sources: https://climate.nasa.gov/"
}
```

---

## 9. Key Improvements

1. **Accurate Tone Detection**: Uses `toxicity_color` from API instead of badge color
2. **Clear Evidence Labels**: Uses consistent terminology across frontend/backend
3. **URL Display**: Shows actual verified URLs in source label
4. **Comprehensive Testing**: 20 test scenarios covering all combinations
5. **Better Tooltips**: More descriptive TL2/TL3 messages in backend
6. **Consistent Logic**: Badge color determination follows TL1 specification exactly

---

## 10. Files Summary

### Created/Updated Files
- ✓ `chrome-extension/trustlens-badges.js` - Updated popup content logic
- ✓ `api/evidence.py` - Improved TL2/TL3 tooltips
- ✓ `api/main.py` - Verified badge color logic
- ✓ `api/toxicity_model/app.py` - Verified toxicity thresholds
- ✓ `test_sample_data.json` - 20 comprehensive test scenarios
- ✓ `test_badge_logic.py` - Automated test script
- ✓ `BADGE_LOGIC_UPDATE.md` - This documentation

---

## Status: ✅ Complete

All requested features have been implemented:
- ✅ Toxicity labels: "Strong language", "Slightly strong language", "Positive tone"
- ✅ Evidence labels: "Verifiable evidence present", "Unverifiable evidence", "Partially verifiable evidence", "No evidence"
- ✅ Source labels: Shows URL if verified, "URL is not verified", or "URL is not present"
- ✅ Comprehensive sample data with 20 test scenarios
- ✅ Models verified and working correctly
- ✅ Complete documentation provided
