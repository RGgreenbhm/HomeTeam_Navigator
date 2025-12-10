# Story E2-S5: Allow Manual Correction of OCR Text

## Status
Draft

## Story
**As a** clinical user,
**I want** to manually correct OCR extraction errors,
**so that** the saved data is accurate.

## Acceptance Criteria
1. Extracted text is editable in a text area
2. Changes are tracked and indicated visually (edited badge)
3. Original OCR text can be restored with "Reset" button
4. Text area supports standard editing (select, copy, paste)
5. Undo/Redo works within the text area (Ctrl+Z, Ctrl+Y)
6. Character count is displayed for long text

## Tasks / Subtasks
- [ ] Convert display to editable textarea (AC: 1)
  - [ ] Replace text display with controlled textarea
  - [ ] Maintain monospace font styling
  - [ ] Auto-expand height based on content
- [ ] Track edit state (AC: 2)
  - [ ] Compare current text to original OCR text
  - [ ] Show "Edited" badge when modified
  - [ ] Store original text for comparison
- [ ] Implement reset functionality (AC: 3)
  - [ ] Add "Reset to OCR" button
  - [ ] Show confirmation if significant changes made
  - [ ] Restore original text on confirm
- [ ] Enable standard editing (AC: 4)
  - [ ] Allow text selection
  - [ ] Support clipboard operations
  - [ ] Handle newlines and formatting
- [ ] Implement undo/redo (AC: 5)
  - [ ] Track edit history stack
  - [ ] Ctrl+Z for undo
  - [ ] Ctrl+Y or Ctrl+Shift+Z for redo
- [ ] Show character count (AC: 6)
  - [ ] Display: "1,234 characters"
  - [ ] Show below textarea

## Dev Notes

### Editable OCR Panel
```typescript
interface EditableOCRProps {
  originalText: string;
  onTextChange: (text: string) => void;
}

function EditableOCR({ originalText, onTextChange }: EditableOCRProps) {
  const [text, setText] = useState(originalText);
  const [history, setHistory] = useState<string[]>([originalText]);
  const [historyIndex, setHistoryIndex] = useState(0);

  const isEdited = text !== originalText;

  const handleReset = () => {
    if (isEdited && !confirm('Discard your edits?')) return;
    setText(originalText);
    onTextChange(originalText);
  };

  // Debounced history tracking
  const pushHistory = useDebouncedCallback((newText: string) => {
    setHistory(h => [...h.slice(0, historyIndex + 1), newText]);
    setHistoryIndex(i => i + 1);
  }, 500);

  // ...
}
```

### Undo/Redo Implementation
```typescript
const handleUndo = () => {
  if (historyIndex > 0) {
    setHistoryIndex(i => i - 1);
    setText(history[historyIndex - 1]);
  }
};

const handleRedo = () => {
  if (historyIndex < history.length - 1) {
    setHistoryIndex(i => i + 1);
    setText(history[historyIndex + 1]);
  }
};

// Keyboard handler
useEffect(() => {
  const handler = (e: KeyboardEvent) => {
    if (e.ctrlKey && e.key === 'z') {
      e.preventDefault();
      handleUndo();
    } else if (e.ctrlKey && (e.key === 'y' || (e.shiftKey && e.key === 'z'))) {
      e.preventDefault();
      handleRedo();
    }
  };
  // ...
}, []);
```

### Auto-expanding Textarea
```typescript
// Use refs to calculate scroll height
const textareaRef = useRef<HTMLTextAreaElement>(null);

useEffect(() => {
  if (textareaRef.current) {
    textareaRef.current.style.height = 'auto';
    textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
  }
}, [text]);
```

### Character Count Display
```
┌─────────────────────────────────────────┐
│  OCR Text  [Edited] [Reset to OCR]      │
├─────────────────────────────────────────┤
│  Patient: DOE, JOHN                     │
│  MRN: 12345                             │
│  ...                                    │
├─────────────────────────────────────────┤
│  1,234 characters                       │
└─────────────────────────────────────────┘
```

## Testing
- **Location**: `src/renderer/components/capture/__tests__/`
- **Framework**: Vitest + React Testing Library
- **Required Tests**:
  - Text is editable
  - "Edited" badge appears on change
  - Reset restores original text
  - Undo reverts last change
  - Redo restores undone change
  - Character count updates

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
