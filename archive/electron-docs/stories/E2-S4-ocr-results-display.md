# Story E2-S4: Display OCR Results with Confidence Highlighting

## Status
Draft

## Story
**As a** clinical user,
**I want** to see extracted text with low-confidence words highlighted,
**so that** I know which parts need manual review.

## Acceptance Criteria
1. Extracted text displays in scrollable panel next to image
2. Low-confidence words (< 80%) are highlighted in yellow
3. Confidence score is shown as percentage (e.g., "95% confidence")
4. User can toggle between image view and OCR text view
5. Loading spinner shows during OCR processing
6. Error state displays clear message with retry option

## Tasks / Subtasks
- [ ] Create OCR results panel (AC: 1)
  - [ ] Create src/renderer/components/capture/OCRResultsPanel.tsx
  - [ ] Display text in scrollable container
  - [ ] Apply monospace font for alignment
- [ ] Implement confidence highlighting (AC: 2)
  - [ ] Parse OCR response for word-level confidence
  - [ ] Apply yellow background to words < 80% confidence
  - [ ] Show tooltip with exact confidence on hover
- [ ] Display overall confidence (AC: 3)
  - [ ] Calculate average confidence from all words
  - [ ] Show badge: "95% confidence"
  - [ ] Color code: green (>90%), yellow (70-90%), red (<70%)
- [ ] Add view toggle (AC: 4)
  - [ ] Create toggle buttons: [Image] [OCR Text]
  - [ ] Smooth transition between views
  - [ ] Remember last selected view
- [ ] Handle loading state (AC: 5)
  - [ ] Show spinner centered in panel
  - [ ] Display "Extracting text..." message
  - [ ] Show elapsed time if > 3s
- [ ] Handle error state (AC: 6)
  - [ ] Display error icon and message
  - [ ] Show [Retry] button
  - [ ] Clear error on new paste

## Dev Notes

### OCR Results Panel Layout
```
┌─────────────────────────────────────────┐
│  [Image]  [OCR Text]    95% confidence  │
├─────────────────────────────────────────┤
│                                         │
│  Patient: DOE, JOHN                     │
│  MRN: 12345                             │
│  DOB: 05/15/1960                        │
│                                         │
│  A1C: 7.2%                              │
│  BP: 138/88                             │
│                                         │
│  Medications:                           │
│  - Metformin 1000mg [highlighted]       │
│  - Lisinopril 20mg                      │
│                                         │
└─────────────────────────────────────────┘
```

### Confidence Highlighting Component
```typescript
interface HighlightedTextProps {
  words: Array<{
    text: string;
    confidence: number;
  }>;
  threshold?: number;  // default 0.8
}

function HighlightedText({ words, threshold = 0.8 }: HighlightedTextProps) {
  return (
    <span>
      {words.map((word, i) => (
        <span
          key={i}
          className={word.confidence < threshold ? 'bg-yellow-200' : ''}
          title={`${(word.confidence * 100).toFixed(0)}% confidence`}
        >
          {word.text}{' '}
        </span>
      ))}
    </span>
  );
}
```

### Confidence Badge Colors
```typescript
function getConfidenceColor(confidence: number): string {
  if (confidence >= 0.9) return 'bg-green-100 text-green-800';
  if (confidence >= 0.7) return 'bg-yellow-100 text-yellow-800';
  return 'bg-red-100 text-red-800';
}
```

### Loading State
```typescript
interface LoadingState {
  isLoading: boolean;
  startTime: number | null;
  elapsedMs: number;
}

// Show elapsed time after 3 seconds
{isLoading && elapsedMs > 3000 && (
  <span className="text-sm text-neutral-500">
    {Math.floor(elapsedMs / 1000)}s elapsed...
  </span>
)}
```

## Testing
- **Location**: `src/renderer/components/capture/__tests__/`
- **Framework**: Vitest + React Testing Library
- **Required Tests**:
  - Low-confidence words are highlighted
  - Overall confidence calculates correctly
  - Toggle switches views
  - Loading spinner appears during processing
  - Error state shows retry button

## Change Log
| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2025-11-30 | 1.0 | Initial story draft | Bob (SM) |

---

## Dev Agent Record
### Agent Model Used
### Debug Log References
### Completion Notes
### File List

---

## QA Results
