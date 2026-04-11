# Project Overview

## Project Name
Local E-commerce Image Collector

## Project Goal
Build a fully local toolchain that helps the user collect product images from supported e-commerce product pages, send the collected data from a Chrome extension to a local service, download the images locally, process them, and save them into a structured folder layout.

The system is intended for local use only and is not meant for public Chrome Web Store distribution.

---

## High-Level Objective
The project consists of two major components:

1. **Chrome Extension**
   - Detect the current website
   - Extract product image URLs from supported product pages
   - Package the extracted data
   - Send the payload to the local service

2. **Local Service**
   - Receive the extraction request
   - Download images
   - Process images with a configurable pipeline
   - Save images and metadata in a predictable local folder structure

---

## Target User
Primary user: the project owner operating the tool locally.

Typical workflow:
- Open a supported product page
- Trigger the extension
- Let the extension extract image URLs
- Send data to the local service
- Let the local service download and process the images
- Review output folders and processed images locally

---

## Core User Flow
1. User opens a supported product page in Chrome
2. Extension identifies the current website
3. Extension selects the matching site handler
4. Extension extracts candidate product image URLs
5. Extension sends the standardized payload to the local service
6. Local service validates the request and creates a processing job
7. Local service downloads the images
8. Local service applies the image-processing pipeline
9. Local service saves raw files, processed files, and metadata
10. User reviews the output

---

## MVP Scope
The first version should remain intentionally small.

### Included in MVP
- Support 1 to 2 websites only
- Detect supported site based on URL/hostname
- Extract product image URLs from product pages
- Send extracted data to local service via localhost HTTP API
- Download images locally
- Perform single-image white-border trimming
- Save output in a structured folder layout
- Write basic logs for debugging

### Excluded from MVP
- Public extension distribution
- Cloud services
- User accounts
- Remote database
- Advanced GUI dashboard
- Full automation for all websites
- Complex image stitching heuristics beyond a first working implementation

---

## Main Design Principles

### 1. Local-first
Everything should run on the user's machine.

### 2. Clear separation of responsibilities
- Extension: site detection, extraction, and payload delivery
- Local service: download, image processing, storage, logging

### 3. Site-specific extraction logic
Different websites may require different extraction strategies, so extraction logic must be modular.

### 4. Pipeline-based image processing
Image processing should be designed as a pipeline rather than hard-coded in a single function.

### 5. Debuggability
Each major step should produce logs so failures can be traced.

---

## Supported Image Processing Scenarios

### Scenario A: Single-image white-border trimming
Some product images contain unnecessary white margins. The local service should detect those borders and crop the visible content area.

### Scenario B: Multiple images that form a continuous larger image
Some websites may split a tall or composite image into several consecutive images. The system may need to:
- detect ordering
- stitch images together
- analyze the stitched result
- split the image again based on white space or content boundaries

This scenario can be implemented after the MVP if needed.

---

## Recommended Technology Stack

### Chrome Extension
- Manifest V3
- JavaScript
- Content scripts
- Background service worker
- Optional popup UI

### Local Service
- Python
- FastAPI
- httpx or requests
- Pillow
- OpenCV
- pathlib
- standard logging

---

## Success Criteria
The project is successful when:
- the user can open a supported product page
- the extension can extract image URLs correctly
- the local service can receive the payload
- images are downloaded locally
- images can be trimmed for white borders
- results are stored in a predictable folder structure
- the user can extend the project to new sites with limited code changes

---

## Expected Deliverables
1. Chrome extension source code
2. Local service source code
3. Technical documentation
4. Site handler interface
5. Image processing pipeline interface
6. Sample configuration and output folder structure
