# Story E2-S3: Integrate Azure Cognitive Services Computer Vision API

## Status
Draft

## Story
**As a** clinical user,
**I want** text automatically extracted from my screenshots using OCR,
**so that** I can quickly see and edit captured patient data.

## Acceptance Criteria
1. Azure Computer Vision API extracts text from images
2. OCR completes within 5 seconds for typical screenshots (1920x1080)
3. API errors are handled gracefully with user-friendly messages
4. Azure API credentials are stored securely
5. OCR request includes proper retry logic with exponential backoff
6. Network offline state is detected and reported

## Tasks / Subtasks
- [ ] Set up Azure client (AC: 1, 4)
  - [ ] Create src/main/services/azure-ocr.ts
  - [ ] Configure @azure/cognitiveservices-computervision
  - [ ] Store API key securely via keytar
  - [ ] Load endpoint URL from config
- [ ] Implement OCR request (AC: 1, 2)
  - [ ] Create analyzeImage() function
  - [ ] Send image as base64 or buffer
  - [ ] Parse response into text lines
  - [ ] Calculate overall confidence score
- [ ] Add retry logic (AC: 5)
  - [ ] Retry on 429 (rate limit) and 5xx errors
  - [ ] Exponential backoff: 1s, 2s, 4s
  - [ ] Maximum 3 retries
- [ ] Handle errors (AC: 3, 6)
  - [ ] Network offline: "OCR unavailable offline. Try again when connected."
  - [ ] Rate limit: "OCR service busy. Please wait a moment."
  - [ ] Auth error: "OCR configuration error. Contact admin."
  - [ ] Timeout: "OCR timed out. Try again."
- [ ] Create IPC channel (AC: 1)
  - [ ] Add capture:ocr handler
  - [ ] Accept image data, return extracted text
  - [ ] Include confidence scores in response

## Dev Notes

### Azure OCR Configuration
```typescript
// src/main/services/azure-ocr.ts
import { ComputerVisionClient } from '@azure/cognitiveservices-computervision';
import { ApiKeyCredentials } from '@azure/ms-rest-js';

const endpoint = process.env.AZURE_CV_ENDPOINT || 'https://eastus.api.cognitive.microsoft.com/';

export class AzureOCRService {
  private client: ComputerVisionClient;

  constructor(apiKey: string) {
    const credentials = new ApiKeyCredentials({ inHeader: { 'Ocp-Apim-Subscription-Key': apiKey } });
    this.client = new ComputerVisionClient(credentials, endpoint);
  }

  async extractText(imageBuffer: Buffer): Promise<OCRResult> {
    const result = await this.client.readInStream(imageBuffer);
    // ... poll for results
  }
}
```

### IPC Handler
```typescript
// Main process
ipcMain.handle('capture:ocr', async (_, { imageData }: { imageData: string }) => {
  try {
    const buffer = Buffer.from(imageData.replace(/^data:image\/\w+;base64,/, ''), 'base64');
    const result = await ocrService.extractText(buffer);

    return {
      success: true,
      data: {
        text: result.text,
        lines: result.lines,
        confidence: result.confidence,
      },
    };
  } catch (error) {
    return {
      success: false,
      error: mapOCRError(error),
    };
  }
});
```

### OCR Response Structure
```typescript
interface OCRResult {
  text: string;              // Full extracted text
  lines: Array<{
    text: string;
    boundingBox: number[];   // [x1, y1, x2, y2, ...]
    confidence: number;      // 0-1
  }>;
  confidence: number;        // Average confidence
}
```

### Retry Implementation
```typescript
async function withRetry<T>(
  fn: () => Promise<T>,
  maxRetries = 3,
  baseDelay = 1000
): Promise<T> {
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      if (attempt === maxRetries || !isRetryable(error)) {
        throw error;
      }
      await sleep(baseDelay * Math.pow(2, attempt));
    }
  }
}
```

### Dependencies
- @azure/cognitiveservices-computervision: ^8.x
- @azure/ms-rest-js: ^2.x

### Performance Target (NFR2)
- Target: < 5 seconds for 1920x1080 image
- Typical Azure response: 2-3 seconds

## Testing
- **Location**: `src/main/services/__tests__/`
- **Framework**: Vitest
- **Required Tests**:
  - Mock API returns text correctly
  - Retry on 429 error
  - Network offline detection
  - Error messages are user-friendly
- **Integration Test**: Real API call (optional, needs credentials)

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
