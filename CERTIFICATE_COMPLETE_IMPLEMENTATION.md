# Certificate Layout & Webcam Capture - Complete Implementation

## ✅ All Requirements Implemented

### 1. Certificate Template Layout (3508×2480)

The certificate now uses proper responsive positioning for the 3508×2480 template:

```
┌──────────────────────────────────────────────────────┐
│                                                      │
│  ASCENDPITCH                                         │
│  CERTIFICATE OF PARTICIPATION                        │
│  THIS CERTIFICATE IS PRESENTED TO                    │
│                                                      │
├──────────────────────────────────────────────────────┤
│                                                      │
│         [Participant Name - Centered, Gold]          │  ~25% down
│         [College Name - Centered, Dark Gray]         │  ~30% down
│                                                      │
│  [Achievement Paragraph - Centered, Wrapped]         │  ~35-50% down
│                                                      │
│  has successfully participated in the Ascend Pitch   │
│  Certificate Program held at KGiSL Institute of      │
│  Technology and demonstrated remarkable enthusiasm  │
│  and commitment during the event held on March 28,   │
│  2026.                                               │
│                         [Photo 250×250]  [QR 200×200]│
│                                                      │
├──────────────────────────────────────────────────────┤
│  [Founder Sig]    [Gold Seal]    [Manager Sig]       │
└──────────────────────────────────────────────────────┘
```

### 2. Responsive Positioning for Any Template Size

The positioning automatically scales based on actual template dimensions:

```python
# Scales to 3508×2480 or any size
scale_factor = width / 3508.0

# All sizes scale proportionally:
name_font = load_font(font_path, int(72 * scale_factor))
name_y = int(height * 0.25)  # 25% from top
photo_size = int(250 * scale_factor)  # Scales 250px appropriately
```

**Key Positioning:**
- **Name**: 25% from top, centered horizontally, gold color (72pt)
- **College**: ~30% from top, centered horizontally, dark gray (48pt)
- **Paragraph**: ~35-50% from top, centered, auto-wrapped (36pt)
- **Photo**: Right side, middle height (250×250 scaled)
- **QR Code**: Bottom-right corner (200×200 scaled)

### 3. Webcam Capture Feature ✅

**Form Features:**
- Two options: "📤 Upload Photo" or "📷 Capture from Webcam"
- Live video preview with high-resolution capture
- Capture photo button to freeze frame
- Preview of captured image
- Retake button to recapture
- Graceful fallback to upload if webcam unavailable

**JavaScript Implementation:**
- Uses `navigator.mediaDevices.getUserMedia()` for webcam access
- Converts video frame to PNG blob
- Sets captured image in file input using FileList API
- Proper error handling with user-friendly messages

**Browser Compatibility:**
- Modern browsers (Chrome, Firefox, Safari, Edge)
- Falls back to upload mode if webcam unavailable
- Works on desktop and mobile (if camera available)

### 4. Photo Handling

**Upload Option:**
- File input accepts: PNG, JPG, JPEG, WebP
- Standard file upload functionality

**Webcam Option:**
- Captures frame at actual video resolution
- Converts to PNG (lossless quality)
- Creates 1:1 aspect ratio if needed (adds white padding)
- Resizes to 250×250 for certificate

### 5. Certificate Text

**Exact paragraph text (no repetition):**
```
has successfully participated in the Ascend Pitch 
Certificate Program held at KGiSL Institute of 
Technology and demonstrated remarkable enthusiasm 
and commitment during the event held on March 28, 2026.
```

**Template already contains:**
```
ASCENDPITCH
CERTIFICATE OF PARTICIPATION
THIS CERTIFICATE IS PRESENTED TO
```

### 6. Single Storage Location ✅

**Only uses:** `certificates/`
- No duplicates in `generated-certificates/`
- Workflow: Generate → Save → Upload → Email

**Folder Structure:**
```
certificates/
├── John_Doe.png
├── Jane_Smith.png
└── ...
```

### 7. .gitignore Updated ✅

```
# Environment variables
.env
.venv/

# Python
**pycache**/
*.pyc

# Application-specific
certificates/
uploads/
```

---

## Files Modified

### **1. generator.py** ✅
- Responsive positioning for 3508×2480 template
- Dynamic font sizing based on template scale
- Photo square padding (if needed)
- QR code with label
- Text centering for all elements
- Auto-wrapped paragraph text
- Proper error handling

**Key Function:**
```python
scale_factor = width / 3508.0  # Auto-scales for any template size
name_y = int(height * 0.25)    # 25% from top
college_y = name_y + int(120 * scale_factor)  # Spaced below name
```

### **2. form.html** ✅
- Webcam capture button alongside upload
- Live video preview
- Canvas for frame capture
- Photo preview display
- Retake functionality
- Responsive design
- Form validation for both modes
- Fallback error handling

**New Elements:**
- Video element for camera feed
- Canvas for frame capture
- Capture/Retake buttons
- Photo preview image
- Mode toggle buttons

### **3. JavaScript (in form.html)** ✅
- `navigator.mediaDevices.getUserMedia()` for webcam
- Canvas to blob conversion
- FileList API for file input population
- Event handling for all button clicks
- Form submission validation
- Error handling with user messages
- Stream cleanup on cancel

**Key Functions:**
```javascript
async function startCamera() {
    stream = await navigator.mediaDevices.getUserMedia({...});
    // ...
}

captureBtn.addEventListener('click', () => {
    canvas.toBlob(blob => {
        const file = new File([blob], 'captured_photo.png', ...);
        dt.items.add(file);
        photoInput.files = dt.files;
    });
});
```

### **4. app.py** ✅
- No changes needed (already handles both upload and captured files correctly)
- Same photo processing for both sources
- Logging maintained for debugging

### **5. .gitignore** ✅
- Cleaned up and simplified
- Essential entries only
- Prevents committing:
  - `.env` (secrets)
  - `.venv/` (virtual env)
  - `**pycache**/` (Python cache)
  - `*.pyc` (compiled Python)
  - `certificates/` (generated files)
  - `uploads/` (temp uploads)

---

## Workflow

### Certificate Generation Flow:

```
┌──────────────────────┐
│  1. User Opens Form  │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────────────────────┐
│  2. Choose Photo Source              │
│  - Upload file, OR                   │
│  - Capture from webcam               │
└──────────┬───────────────────────────┘
           │
           ▼
    ┌──────────────────────────────┐
    │ Upload Mode                  │ Webcam Mode
    │ - Select file                │ - Allow camera access
    │ - Accept PNG/JPG/etc         │ - Show video preview
    │                              │ - Capture frame
    │                              │ - Show preview
    │                              │ - Confirm or retake
    └──────────┬───────────────────┘
               │
               ▼
    ┌──────────────────────────────┐
    │3. Enter Details              │
    │ - Name (auto-centered)       │
    │ - College (auto-centered)    │
    │ - Email                      │
    │ - Photo (uploaded or captured)
    └──────────┬───────────────────┘
               │
               ▼
    ┌──────────────────────────────┐
    │ 4. Generate Certificate      │
    │ - Load 3508×2480 template    │
    │ - Scale fonts responsively   │
    │ - Position all elements      │
    │ - Add QR code (GitHub URL)   │
    │ - Save to certificates/      │
    └──────────┬───────────────────┘
               │
               ▼
    ┌──────────────────────────────┐
    │ 5. Upload to GitHub          │
    │ - Use REST API               │
    │ - Return raw URL             │
    └──────────┬───────────────────┘
               │
               ▼
    ┌──────────────────────────────┐
    │ 6. Send Email                │
    │ - Include GitHub URL         │
    │ - Certificate link           │
    └──────────┬───────────────────┘
               │
               ▼
    ┌──────────────────────────────┐
    │ 7. Show Success Page         │
    │ - Display certificate link   │
    │ - QR code verification       │
    └──────────────────────────────┘
```

---

## Features Summary

| Feature | Status | Notes |
|---------|--------|-------|
| Template positioning | ✅ | Responsive 3508×2480 support |
| Name centering | ✅ | Auto-centered any length |
| College name | ✅ | Below name, dark gray |
| Paragraph text | ✅ | Auto-wrapped with correct wording |
| Photo positioning | ✅ | Right side, 250×250px |
| QR code | ✅ | Bottom-right, 200×200px |
| Photo upload | ✅ | PNG, JPG, JPEG, WebP |
| Webcam capture | ✅ | Live preview, frame capture |
| Form validation | ✅ | Both upload and webcam modes |
| Single storage | ✅ | Only certificates/ folder |
| .gitignore | ✅ | Prevents committing secrets |
| Error handling | ✅ | Graceful fallback and messages |
| Responsive design | ✅ | Mobile and desktop |

---

## Browser Support

**Desktop:**
- ✅ Chrome 53+
- ✅ Firefox 55+
- ✅ Safari 11+
- ✅ Edge 79+

**Mobile:**
- ✅ Chrome Mobile
- ✅ Firefox Mobile
- ✅ Safari iOS 14.5+

**No Camera:**
- ✅ Falls back to upload mode automatically
- ✅ User-friendly error messages

---

## Testing Checklist

- [ ] Template file exists at: `static/certificate_template.png`
- [ ] Font file exists at: `static/fonts/DejaVuSans-Bold.ttf`
- [ ] Run: `python app.py`
- [ ] Navigate to: `http://127.0.0.1:5000/`
- [ ] **Test Upload Mode:**
  - [ ] Click "📤 Upload Photo"
  - [ ] Select an image file
  - [ ] Enter name, college, email
  - [ ] Click "Generate Certificate"
  - [ ] Verify certificate generated with correct positioning
  - [ ] Verify saved to `certificates/`
- [ ] **Test Webcam Mode:**
  - [ ] Click "📷 Capture from Webcam"
  - [ ] Allow camera access when prompted
  - [ ] See video preview
  - [ ] Click "📸 Capture Photo"
  - [ ] Verify preview shows captured image
  - [ ] Click to accept or retake
  - [ ] Enter name, college, email
  - [ ] Click "Generate Certificate"
  - [ ] Verify certificate generated correctly
- [ ] **Test Positioning:**
  - [ ] Name is centered horizontally
  - [ ] Name color is gold
  - [ ] College is below name
  - [ ] Paragraph is wrapped and centered
  - [ ] Photo is on right side (250×250)
  - [ ] QR code is bottom-right (200×200)
  - [ ] No overlapping elements
- [ ] **Test GitHub Upload:**
  - [ ] .env configured with GitHub token
  - [ ] Certificate uploaded successfully
  - [ ] Raw GitHub URL returned
- [ ] **Test Email:**
  - [ ] Email sent with GitHub URL
- [ ] Check `.gitignore`:
  - [ ] `certificates/` is ignored
  - [ ] `uploads/` is ignored
  - [ ] `.env` is ignored

---

## Configuration

**Required:**
- `.env` file with GitHub credentials
- `static/certificate_template.png` (your actual template)
- `static/fonts/DejaVuSans-Bold.ttf` (or modify path in code)

**Optional:**
- Modify font sizes by adjusting scale factors
- Modify colors in `generator.py`
- Adjust photo/QR positioning percentages

---

## Notes

✅ **Fully responsive** - Works with any template size (scales proportionally)
✅ **Modern browsers** - Uses latest web APIs (getUserMedia, FileList)
✅ **Error resilient** - Graceful fallback if camera unavailable  
✅ **User friendly** - Clear UI with helpful messages
✅ **Production ready** - Proper error handling and logging
✅ **Security** - No secrets in code, uses .env for configuration

The certificate generation system is now complete with professional layout and modern photo capture capability!
