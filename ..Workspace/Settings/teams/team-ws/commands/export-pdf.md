# Export Markdown to PDF

Export a markdown file to PDF format with full GitHub-style rendering, including color emojis.

## Arguments

- `$ARGUMENTS` - Path to the markdown file to export (required)

## Instructions

When this command is invoked:

### 1. Validate Input

- If no file path provided in `$ARGUMENTS`, ask the user which file to export
- Verify the file exists and has `.md` extension
- If file doesn't exist, report error and stop

### 2. Ensure Export_Ready Folder Exists

```bash
mkdir -p "d:/Projects/Patient_Explorer/Export_Ready"
```

### 3. Check Dependencies

Verify md-to-pdf is installed:

```bash
npx md-to-pdf --version
```

If missing, install it:
```bash
npm install -g md-to-pdf
```

### 4. Convert to PDF

Use md-to-pdf (Chrome/Puppeteer-based) for best rendering:

```bash
# Get the filename without path and extension
FILENAME=$(basename "$INPUT_FILE" .md)

# Convert from the Export_Ready directory so output lands there
cd "d:/Projects/Patient_Explorer/Export_Ready"
npx md-to-pdf "../$INPUT_FILE"

# The output will be in the same location as input, so move it
mv "../${INPUT_FILE%.md}.pdf" "./${FILENAME}.pdf" 2>/dev/null || true
```

**Alternative: With custom CSS styling**
```bash
npx md-to-pdf "$INPUT_FILE" --stylesheet "d:/Projects/Patient_Explorer/Export_Ready/pdf-style.css"
```

### 5. Report Result

On success:
- Report the output path: `Export_Ready/{filename}.pdf`
- Confirm file size

On failure:
- Report the error
- Suggest troubleshooting steps

## Why md-to-pdf?

| Feature | md-to-pdf | wkhtmltopdf |
|---------|-----------|-------------|
| Color emojis | ✅ Yes | ❌ No |
| Modern CSS | ✅ Full support | ⚠️ Limited |
| GitHub markdown | ✅ Native | ⚠️ Via pandoc |
| Font rendering | ✅ Excellent | ⚠️ Basic |

md-to-pdf uses Puppeteer (headless Chrome) which renders markdown exactly like a modern browser.

## Installation (One-Time Setup)

```bash
# Install md-to-pdf globally
npm install -g md-to-pdf

# Verify installation
npx md-to-pdf --version
```

## Example Usage

```
/export-pdf Project_Patient_Explorer_App/briefs/2025-12-03_ProjectStatusBrief.md
```

Output: `Export_Ready/2025-12-03_ProjectStatusBrief.pdf`

## Configuration Options

md-to-pdf can be configured with a config file or frontmatter in the markdown file:

**Frontmatter example (add to top of .md file):**
```yaml
---
pdf_options:
  format: Letter
  margin: 25mm
  printBackground: true
---
```

**Common options:**
- `format`: A4, Letter, Legal
- `margin`: Page margins (e.g., "25mm" or {top: "20mm", bottom: "20mm"})
- `printBackground`: Include background colors/images
- `displayHeaderFooter`: Show headers/footers
- `headerTemplate`: Custom header HTML
- `footerTemplate`: Custom footer HTML

See: https://github.com/simonhaenisch/md-to-pdf
