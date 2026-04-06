# Camera File Naming Conventions

> **Purpose:** Reference document for PokerFX to understand how different cameras name video files by default. This guides parsing, ingestion, and auto-detection logic when PokerFX expands to support users with diverse camera setups.

> **Last Updated:** 2026-04-06

> **Used By:** File upload pipeline, import wizards, ASR job configuration, media management

---

## TL;DR — Naming Pattern Summary

| Camera / Platform | Default Video Filename Pattern | Extensions | Notes |
|---|---|---|---|
| **Insta360 (X3, X4, ONE X2)** | `VID_YYYYMMDD_HHMMSS_00_XXX.insv` | `.insv`, `.mp4` (edited/exported) | Dual-lens cameras produce two `.insv` files (front/back) |
| **Insta360 GO 3** | `VID_YYYYMMDD_HHMMSS_00_XXX.mp4` | `.mp4` | Single-lens, no dual files |
| **GoPro Hero (10–13, Black)** | `GH01NNNN.MP4` / `GX01NNNN.MP4` | `.MP4` | 4GB chapter split: NNNN increments, H=1080p, X=4K+ |
| **GoPro MAX** | `GX01NNNN.MP4` + dual lens `.360` files | `.MP4`, `.360` | 360° camera with dual-lens raw files |
| **iPhone (all recent models)** | `IMG_XXXX.MOV` or `IMG_XXXX.MP4` | `.MOV` (HEVC ProRes), `.MP4` (HEVC/H.264) | XXXX = sequential counter (0001–9999), resets on format |
| **Android / Samsung** | `VID_YYYYMMDD_WA_BBS.mp4` (newer) / `VID_XXXX.mp4` (older) | `.mp4` | WA=Burst/group, BBS=sequence in group |
| **Canon DSLR / Mirrorless** | `MVI_XXXX.MOV` (video) / `IMG_XXXX.JPG` (photos) | `.MOV`, `.MP4` | XXXX = sequential (1000–9999), folder per 1000 files |
| **Sony Alpha / FX** | `C0001.MP4` / `CXXXXXXX.MP4` | `.MP4`, `.MTS` | Clip numbering, reset per folder/medium |
| **Nikon DSLR / Mirrorless** | `DSC_XXXX.MOV` (video) / `DSC_XXXX.JPG` (photos) | `.MOV`, `.MP4` | XXXX = sequential (0001–9999) |
| **DJI (Action 3/4, Osmo, Pocket)** | `DJI_YYYYMMDD_HHMMSS_XXX_XXXX.MP4` | `.MP4` | Full timestamp in filename, includes sequence |

---

## 1. Insta360 Cameras

### Models Covered
- **Insta360 X3** — 360° action camera (5.7K)
- **Insta360 X4** — 360° action camera (8K)
- **Insta360 ONE X2** — 360° action camera (5.7K)
- **Insta360 ONE RS** — Modular action camera
- **Insta360 GO 3** — Tiny form-factor, single-lens

### Filename Pattern
```
VID_YYYYMMDD_HHMMSS_00_XXX.insv
```

**Breakdown:**
- `VID_` — Fixed prefix for video files
- `YYYYMMDD` — Recording date (e.g., `20250115` = Jan 15, 2025)
- `HHMMSS` — Recording time in 24h (e.g., `143022` = 14:30:22)
- `_00` — Camera unit index (always `00` on single-camera setups)
- `XXX` — Sequential recording number (padded to 3 digits: `001`, `002`, etc.)
- `.insv` — Insta360 proprietary video container (essentially an MP4 wrapper with 360° metadata, gyro data, HDR/LUT info)

### Dual-Lens Behavior (X3, X4, ONE X2)
360° cameras save **two files per recording**:
```
VID_20250115_143022_00_001.insv   ← Front/primary lens
VID_20250115_143022_00_002.insv   ← Back/secondary lens
```

Both files share the same timestamp — the third digit distinguishes the lens stream (commonly `01` vs `02` for dual-lens files). After processing in the Insta360 Studio app, these are stitched into a single equirectangular `.mp4`.

### Other File Types
- `.lrv` — Low-resolution preview (auto-generated for quick playback)
- `.insp` — Single 360° photo (not video)
- Exported/stitched output: standard `.mp4` with conventional naming

### Key Implications for PokerFX
- Insta360 files are **timestamp-embedded** — no need to read EXIF for date/time
- Dual-lens pairs must be detected and processed together (stitched before ASR)
- The `.insv` container is playable by most video players (it *is* H.264/H.265 in an MP4 container with extra metadata) but requires stitching for a usable single view
- Exported videos from Insta360 Studio will have user-chosen or app-generated names that may differ from the raw `.insv` pattern

**Sources:**
- Insta360 Studio User Manual — [Insta360 Support — What is the .insv file](https://support.insta360.com/article/what-is-the-insv-file)
- Insta360 X3 User Guide — [Insta360 X3 Manual](https://www.insta360.com/support/supportcourse?supportId=Insta360X3&productId=Insta360X3)
- Community documentation on GitHub repos processing Insta360 files: various

---

## 2. GoPro Cameras

### Models Covered
- **GoPro HERO 10/11/12/13 Black** — Standard action cameras
- **GoPro HERO 9 Black**
- **GoPro MAX** — 360° action camera
- **GoPro HERO 8/7/6** — Older models (mostly same pattern)

### Filename Pattern
```
GH01NNNN.MP4    or    GX01NNNN.MP4
```

**Breakdown:**
- `G` — Fixed prefix (GoPro)
- `H` or `X` — Resolution tier indicator:
  - `H` = Standard (typically 1080p or below, or single stream)
  - `X` = High resolution (4K+, Wide FOV, or high frame rate)
  - The second character sometimes varies by model (`GP` for very old models)
- `01` — Video stream/chapter number within a recording session
- `NNNN` — Sequential file counter (0001–9999), **globally** incremented across all recordings until manually reset

### 4GB Chapter Splitting
GoPro cameras automatically **split recordings at ~4GB** (FAT32 filesystem limit, kept for compatibility). A single 20-minute recording might produce:
```
GX010345.MP4   ← Part 1 (minutes 0–4)
GX010346.MP4   ← Part 2 (minutes 4–8)
GX010347.MP4   ← Part 3 (minutes 8–12)
```

The counter `NNNN` increments per chapter, **not per recording**. There is **no timestamp** in the filename — you must read file metadata (EXIF/creation date) to determine when the recording happened.

### GoPro MAX (360° Camera)
The MAX produces:
```
GX01NNNN.MP4     ← Stitched video (standard MP4)
G001NNNN.360     ← Raw dual-lens data (requires GoPro Player to decode)
```

### GoPro Labs Custom Naming
GoPro supports custom naming via **GoPro Labs** firmware modifications (`/config/naming/`), allowing users to enable date-based naming, but this requires hacked firmware and is not stock behavior.

### Key Implications for PokerFX
- **No timestamps in filenames** — must rely on file metadata (creation date, EXIF) for temporal ordering
- **Chapter splitting is the biggest pain point** — a single recording session spans multiple files with sequential numbers
- The counter `NNNN` is **global/persistent**, not per-session — you cannot assume `NNNN+1` means the next recording session
- Multiple cameras will have overlapping/interleaved counters

**Sources:**
- GoPro Official Support — [GoPro File Naming Convention](https://gopro.com/help/articles/Question_Answer/Understanding-GoPro-File-Naming-Convention)
- GoPro Community — [Understanding GoPro File Names](https://community.gopro.com/t5/en/Understanding-GoPro-File-Naming/td-p/395412)
- GoPro Labs documentation — [GoPro Labs Custom Firmware](https://gopro.github.io/labs/control/)

---

## 3. Apple iPhone

### Models Covered
- **iPhone 17 Pro Max** (and all recent iPhone models)
- iPhone 16, 15, 14, 13 Pro series
- iPhone SE (3rd gen and later)

### Filename Pattern
```
IMG_XXXX.MOV    or    IMG_XXXX.MP4
```

**Breakdown:**
- `IMG_` — Fixed prefix for both photos and videos
- `XXXX` — **Sequential counter** (0001–9999), not a timestamp
- `.MOV` — Default when recording in:
  - HEVC (H.265) — "High Efficiency" setting
  - ProRes / ProRes RAW (Pro models)
  - Apple Log
- `.MP4` — When recording in:
  - H.264 compatibility mode
  - Shared/converted via AirDrop or third-party apps
  - "Most Compatible" format setting

### Counter Behavior
- The counter (`XXXX`) **starts at 0001** and increments for **every photo and video** taken
- Resets to 0001 when the user **formats the device** or when it reaches 9999
- Counter **persists across restarts** — it is stored in the filesystem
- Photos and videos share the same counter namespace — if you take 500 photos then record a video, the video will be `IMG_0501.*`
- Multiple iPhones will have **independent** counters (no synchronization)

### Live Photos
Live Photos are saved as `.HEIC` (image) + companion `.MOV` (short video clip), both sharing the same `IMG_XXXX` base.

### Key Implications for PokerFX
- **No timestamps in filenames** — counter is meaningless for temporal ordering
- Photos and videos mixed in the same counter space
- Must rely on **file metadata** (EXIF `CreateDate`, `MediaCreationDate`) for actual timing
- Counter resets make long-term tracking unreliable
- ProRes files can be **very large** — important for upload pipeline

**Sources:**
- Apple Official Support — [iOS file naming conventions](https://support.apple.com/)
- Photography community documentation on iPhone file management
- EXIF specification for iPhone media metadata

---

## 4. Android Cameras

### Models Covered
- **Samsung Galaxy S / Note / Z series**
- **Google Pixel** phones
- Most Android devices (manufacturer-dependent)

### Modern Pattern (Android 11+, most Samsung)
```
VID_YYYYMMDD_WA_BBS.mp4    (newer)
```
or
```
VID_XXXX.mp4               (older Android versions)
```

**Breakdown (newer Samsung):**
- `VID_` — Fixed prefix
- `YYYYMMDD` — Date of recording (e.g., `20250115`)
- `WA` — Group/WA number (burst group ID, typically `00`–`09`)
- `BBS` — Sequence number within group (base-36 encoded), e.g., `00` = first file in group
- `.mp4` — Standard MP4 extension

**Breakdown (older/generic Android):**
- `VID_` — Fixed prefix
- `XXXX` — Sequential counter (0001–9999)
- `.mp4` — Standard MP4 extension

### Google Pixel
Google Pixel phones typically use:
```
PXL_YYYYMMDD_HHMMSSXXXX.mp4
```
- `PXL_` — Pixel prefix
- `YYYYMMDD` — Date
- `HHMMSS` — Time
- `XXXX` — Short random/sequential suffix
- This is a more informative pattern that **does include timestamps**

### Samsung Specifics
Samsung cameras also create:
- `.mp4` — Standard video recordings
- `.jpg` — Frame captures / thumbnails

### Key Implications for PokerFX
- **Android naming is manufacturer-specific** — no universal standard
- Samsung's newer pattern **includes timestamps** — good for ordering
- Older Android patterns use counters — similar to iPhone limitations
- Google Pixel's `PXL_` pattern is the most informative (has full timestamp)
- Must implement per-manufacturer detection when uploading Android videos

**Sources:**
- Android Open Source Project (AOSP) camera module documentation
- Samsung Developer documentation — [Camera File Naming](https://developer.samsung.com/)
- Various community forums documenting Android camera conventions

---

## 5. Canon Cameras (DSLR / Mirrorless)

### Models Covered
- **Canon EOS R5 / R6 / R6 II / R7 / R8 / R50 / R100** — Mirrorless
- **Canon EOS 5D Mark IV / 6D Mark II** — DSLR
- **Canon PowerShot** series — Point-and-shoot

### Filename Pattern
```
MVI_XXXX.MOV     (video mode)
IMG_XXXX.JPG     (photo mode)
```

**Breakdown:**
- `MVI_` — **M**o**v**ie prefix (video)
- `IMG_` — Image prefix (photos)
- `XXXX` — **Sequential counter** (starts at 0001, goes to 9999)
- Folder structure: `100CANON/`, `101CANON/`, etc. — new folder every 1000 files (per DCF specification)
- `.MOV` — Default video format (H.264/H.265 in QuickTime wrapper)
- `.MP4` — Some newer models (EOS R series) also produce `.MP4` for certain recording modes

### DCF Specification
Canon follows the **Design Rule for Camera File System** (DCF, JEITA CP-3461), an industry standard:
- Folders: `\DCIM\100CANON\`, `\DCIM\101CANON\`, etc.
- Filenames: 8.3 format (8 char base + 3 char extension)
- Counter range: 0001–9999
- New folder after 9999 files

### Counter Reset
- Counter can be set to "Continuous" (never resets) or "Auto Reset" (resets on folder change)
- In practice, most users leave it on "Continuous"

### Key Implications for PokerFX
- **No timestamps in filenames** — counter-based like iPhone
- Folder-based organization (`\DCIM\NNNCANON\`) must be handled during file ingestion
- DCF standard also applies to Nikon and Sony (they use different prefixes but same structure)
- `.MOV` wrapper requires handling alongside `.MP4`

**Sources:**
- JEITA CP-3461 — [Design Rule for Camera File System (DCF)](https://www.jeita.or.jp/)
- Canon EOS R5 User Manual — [File Naming section](https://usa.canon.com/support)
- Canon EOS documentation — camera file management specifications

---

## 6. Sony Cameras (Alpha / FX / Cyber-shot)

### Models Covered
- **Sony A7 IV / A7S III / A7R V** — Full-frame mirrorless
- **Sony FX3 / FX30 / FX6** — Cinema line
- **Sony ZV-E10 / ZV-1** — Vlogger-focused
- **Sony Cyber-shot** series — Point-and-shoot

### Filename Pattern
```
C0001.MP4    or    CXXXXXXX.MP4
```

**Breakdown:**
- `C` — Clip prefix
- `XXXX` — Sequential counter (0001–9999 or longer on newer models)
- `.MP4` — Standard format
- `.MTS` — AVCHD format (older/lower-resolution recordings, found in `PRIVATE/AVCHD/` folder)

### Folder Structure
```
/DCIM/100MSDCF/     ← Sony-specific folder naming
    ├── C0001.MP4
    ├── C0002.MP4
    └── ...
```

- `MSDCF` = Memory Stick Digital Camera Format
- Similar DCF folder numbering as Canon/Nikon but different suffix

### XAVC S vs AVCHD
- **XAVC S** — `.MP4` files, high bitrate (up to 600Mbps in 4K), recommended for professional use
- **AVCHD** — `.MTS` files, lower bitrate, interlaced video, found in `PRIVATE/AVCHD/BDMV/STREAM/`

### Key Implications for PokerFX
- **No timestamps in filenames** — counter-based
- Dual format support needed (`.MP4` + `.MTS`)
- High-resolution 4K files at high bitrates — important for upload pipeline sizing
- Sony cameras are popular among vloggers (ZV series specifically designed for vlogging) — PokerFX will likely encounter them

**Sources:**
- Sony α7S III User Manual — [File Naming section](https://support.d-imaging.sony.co.jp/support/)
- Sony FX3 User Guide — [Recording File Types](https://helpguide.sony.net/)
- DCF specification (JEITA CP-3461)

---

## 7. Nikon Cameras (DSLR / Mirrorless)

### Models Covered
- **Nikon Z8 / Z9 / Z7 II / Z6 III** — Mirrorless
- **Nikon D850 / D780** — DSLR

### Filename Pattern
```
DSC_XXXX.MOV     (video mode)
DSC_XXXX.JPG     (photo mode — NEF for RAW)
```

**Breakdown:**
- `DSC_` — **D**igital **S**till **C**amera prefix (shared between photo & video)
- `XXXX` — **Sequential counter** (0001–9999)
- `.MOV` — Video format (H.264/H.265 in QuickTime wrapper)
- `.MP4` — Some newer models (Z series) offer `.MP4` option

### Folder Structure
```
/DCIM/100NCD90/     ← Nikon-specific folder naming (model + generation code)
    ├── DSC_0001.MOV
    └── ...
```

Similar DCF-based structure. Folder suffix varies by model (e.g., `NCD90` for D90-era, `NZ8__` for Z8, etc.).

### Key Implications for PokerFX
- Same general pattern as Canon — counter-based, no timestamps
- DCF standard applies — folder structure predictable
- `.MOV` primary, `.MP4` secondary

**Sources:**
- Nikon Z8 User Manual — [File Naming section](https://downloadcenter.nikonimglib.com/)
- DCF specification (JEITA CP-3461)

---

## 8. DJI Cameras

### Models Covered
- **DJI Action 3 / Action 4 / Action 5 Pro** — Action cameras
- **DJI Osmo Action 2** — Compact action camera
- **DJI Pocket 2 / Pocket 3** — Gimbal cameras

### Filename Pattern
```
DJI_YYYYMMDD_HHMMSS_XXX_XXXX.MP4
```

**Breakdown:**
- `DJI_` — Fixed prefix
- `YYYYMMDD` — Recording date
- `HHMMSS` — Recording time
- `XXX` — Sequence number (001, 002, etc.)
- `XXXX` — Additional counter or model-specific suffix
- `.MP4` — Standard MP4 format

### Key Implications for PokerFX
- **Full timestamp in filename** — excellent for temporal ordering without metadata
- Very similar pattern to Insta360 — can be parsed with similar logic
- DJI Action cameras are direct competitors to GoPro — increasingly popular
- DJI Pocket series popular among vloggers — likely to encounter in wild

**Sources:**
- DJI Action 4 User Manual — [Storage and File section](https://www.dji.com/support)
- DJI Osmo Action documentation

---

## 9. Panasonic Lumix Cameras

### Models Covered
- **Panasonic Lumix GH5 / GH6 / GH7** — Mirrorless (popular for video)
- **Panasonic Lumix S5 / S5 II** — Full-frame mirrorless
- **Panasonic Lumix G100** — Vlogger-focused

### Filename Pattern
```
P1000001.MP4    or    P1010001.MP4
```

**Breakdown:**
- `P` — Panasonic prefix
- `100` or `101` — Folder number (corresponds to `100_PANA`, `101_PANA` folders)
- `0001` — Sequential counter
- `.MP4` / `.MTS` — Video format (`.MP4` for MP4 mode, `.MTS` for AVCHD)

### Folder Structure
```
/DCIM/100_PANA/
    ├── P1000001.MP4
    └── ...
```

### Key Implications for PokerFX
- Counter-based, no timestamps in filenames
- `.MTS` (AVCHD) support needed
- GH series popular among filmmakers — may encounter in professional settings

**Sources:**
- Panasonic Lumix GH6 User Manual — [Recording/Playback](https://av.jpn.support.panasonic.com/support/global/cs/dsc/)

---

## Pattern Analysis & Categorization

For PokerFX parsing logic, we can categorize cameras by how their naming convention handles temporal information:

### Category A: Full Timestamp in Filename (Easy)
- **Insta360**: `VID_YYYYMMDD_HHMMSS_00_XXX.insv` ✓ Full date+time
- **DJI**: `DJI_YYYYMMDD_HHMMSS_XXX_XXXX.MP4` ✓ Full date+time

**→ PokerFX can sort and order these files by filename alone. No metadata extraction needed for basic ordering.**

### Category B: Date-Only in Filename
- **Samsung (modern)**: `VID_YYYYMMDD_WA_BBS.mp4` — Date only
- **GoPro MAX (some modes)**: May include date in some exported names
- **Google Pixel**: `PXL_YYYYMMDD_HHMMSSXXXX.mp4` — Full date+time (often)

**→ Can sort by date, but need metadata for time-of-day ordering within same day.**

### Category C: Counter Only — No Temporal Info (Hard)
- **iPhone**: `IMG_XXXX.MOV` — Sequential counter
- **GoPro Hero**: `GH01NNNN.MP4` — Sequential counter, chapters complicate things
- **Canon**: `MVI_XXXX.MOV` — Sequential counter
- **Sony**: `C0001.MP4` — Sequential counter
- **Nikon**: `DSC_XXXX.MOV` — Sequential counter
- **Panasonic**: `P1000001.MP4` — Sequential counter
- **Android (older)**: `VID_XXXX.mp4` — Sequential counter

**→ MUST extract file metadata (creation date, modification date, EXIF `CreateDate`, `MediaCreationDate`) for any temporal ordering. Counters are often meaningless across recording sessions and are shared between photo+video. Chapter splitting (GoPro) makes this worse.**

---

## Implications for PokerFX Architecture

### 1. Upload / Ingestion
When a user uploads a video file, PokerFX should:
1. **Detect the camera source** by filename pattern matching (regex)
2. **Extract timestamp** from filename if available (Category A/B)
3. **Fall back to metadata extraction** if filename has no timestamp (Category C)
4. **Handle chapter splitting** (detect GoPro sequential files, group them)
5. **Handle dual-lens files** (Insta360 `.insv` pairs, GoPro MAX `.360` files)

### 2. Suggested Regex Patterns for Detection

```python
# Insta360 X3/X4/ONE X2 (dual-lens 360°)
INSTA360_360 = r'^VID_(\d{8})_(\d{6})_00_(\d{3})\.insv$'

# Insta360 GO 3 (single lens, MP4)  
INSTA360_GO3 = r'^VID_(\d{8})_(\d{6})_00_(\d{3})\.mp4$'

# GoPro Hero (standard action camera)
GOPRO_HERO = r'^G[HXP](\d{2})(\d{4})\.MP4$'

# GoPro MAX (360°)
GOPRO_MAX = r'^G(\d{2})(\d{4})\.360$'

# iPhone / iOS
IPHONE = r'^IMG_(\d{4})\.(MOV|MP4)$'

# Samsung modern Android
SAMSUNG_MODERN = r'^VID_(\d{8})_\d{2}_\d{2}\.mp4$'

# Android older / generic
ANDROID_GENERIC = r'^VID_(\d{4})\.mp4$'

# Google Pixel
GOOGLE_PIXEL = r'^PXL_(\d{8})_(\d{6})\w*\.mp4$'

# Canon DSLR/Mirrorless (video)
CANON_VIDEO = r'^MVI_(\d{4})\.(MOV|MP4)$'

# Sony Alpha/FX
SONY = r'^C(\d{4,7})\.MP4$'

# Nikon DSLR/Mirrorless
NIKON = r'^DSC_(\d{4})\.(MOV|MP4)$'

# DJI Action/Osmo
DJI = r'^DJI_(\d{8})_(\d{6})_\d{3}_\d{4}\.MP4$'

# Panasonic Lumix
PANASONIC = r'^P(\d{7,8})\.(MP4|MTS)$'
```

### 3. Metadata Fallback (Category C Cameras)
For counter-based cameras, extract:
- **EXIF `CreateDate`** / `DateTimeOriginal` — from file metadata
- **File creation timestamp** — filesystem metadata (less reliable, varies by OS when copying)
- **File modification timestamp** — filesystem metadata (often wrong after transfer)

Python libraries for metadata extraction:
- `exifread` — Read EXIF from various formats
- `hachoir` — Metadata extraction for video files
- `ffmpeg-python` — Probe video files for metadata via `ffprobe`
- `pymediainfo` — Comprehensive media metadata, works for `.insv`, `.MTS`, `.MOV`, `.MP4`

### 4. Multi-Camera Detection
When a user uploads files from multiple cameras:
- Counters will be **non-comparable** across cameras (iPhone `IMG_0500` has no relation to Nikon `DSC_0500`)
- Only **timestamps** provide reliable cross-camera ordering
- Category A cameras (Insta360, DJI) are the most reliable for multi-camera sync

---

## Glossary

| Term | Definition |
|------|-----------|
| **DCF** | Design Rule for Camera File System — JEITA industry standard defining how cameras organize files on storage media |
| **EXIF** | Exchangeable Image File Format — metadata standard for photos and videos |
| **`.insv`** | Insta360 Video — proprietary wrapper (H.264/H.265 in MP4 container with gyro/360° metadata) |
| **`.MTS`** | AVCHD Transport Stream — Sony/Panasonic video format |
| **Chapter splitting** | Automatic file splitting at ~4GB to maintain filesystem compatibility |
| **Equirectangular** | 360° video format — flat projection of spherical video, requires special player |
| **ProRes** | Apple's high-quality video codec — large files, used for professional editing |
| **XAVC S** | Sony's video codec based on H.264/H.265, typically in MP4 container |

---

## References & Sources

1. **Insta360** — Support docs: https://support.insta360.com/
2. **Insta360 X3 Manual** — https://www.insta360.com/support/supportcourse?supportId=Insta360X3&productId=Insta360X3
3. **GoPro File Naming Support** — https://gopro.com/help/articles/Question_Answer/Understanding-GoPro-File-Naming-Convention
4. **GoPro Labs** — https://gopro.github.io/labs/control/
5. **GoPro Community** — https://community.gopro.com/t5/en/Understanding-GoPro-File-Naming/td-p/395412
6. **JEITA CP-3461 (DCF Standard)** — https://www.jeita.or.jp/
7. **Canon EOS Support** — https://usa.canon.com/support
8. **Sony Imaging Support** — https://support.d-imaging.sony.co.jp/support/
9. **Sony Help Guide** — https://helpguide.sony.net/
10. **Nikon Download Center** — https://downloadcenter.nikonimglib.com/
11. **DJI Support** — https://www.dji.com/support
12. **Panasonic Support** — https://av.jpn.support.panasonic.com/support/global/cs/dsc/
13. **Apple Support** — https://support.apple.com/
14. **EXIF Specification** — https://www.exif.org/
15. **Android Open Source Project (AOSP) — Camera** — https://source.android.com/docs/core/interaction/camera

---

*This document should be updated as new camera naming patterns are discovered or when manufacturers update their firmware to change conventions.*
