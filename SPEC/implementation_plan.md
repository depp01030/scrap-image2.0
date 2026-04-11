# Implementation Plan

## 1. Overview
This document defines the phased implementation plan for the Local E-commerce Image Collector project.

The goal is to deliver a working MVP first, then expand site coverage and image-processing sophistication.

---

## 2. Phase Plan Summary

| Phase | Goal | Main Output |
|---|---|---|
| Phase 1 | Build local service skeleton | Working FastAPI localhost service |
| Phase 2 | Build extension skeleton | Working Manifest V3 extension with manual trigger |
| Phase 3 | Define shared payload contract | Extension and service can communicate |
| Phase 4 | Implement image download | Images saved locally in raw folder |
| Phase 5 | Implement white-border trimming | Processed images saved locally |
| Phase 6 | Introduce site handler structure | Modular extraction logic for multiple websites |
| Phase 7 | Add stitching and splitting pipeline | Support sequential image reconstruction |
| Phase 8 | Improve storage, logs, and reliability | Better debugging and maintainability |

---

## 3. Detailed Phase Breakdown

## Phase 1: Local Service Skeleton

### Objective
Set up the Python local service and expose a localhost API endpoint.

### Tasks
- Create project structure for local service
- Set up FastAPI app entry point
- Add configuration loader
- Add logger setup
- Define a health check endpoint
- Define a placeholder job endpoint

### Deliverables
- Running local FastAPI service
- `/health` endpoint
- `/jobs` endpoint stub
- Basic logging configuration

### Acceptance Criteria
- Service starts successfully
- Health endpoint returns success
- Job endpoint accepts test JSON and returns a placeholder response

---

## Phase 2: Chrome Extension Skeleton

### Objective
Set up the Chrome extension and allow a manual trigger.

### Tasks
- Create Manifest V3 project structure
- Register background service worker
- Create popup page
- Add content script or page scanner
- Add manual trigger button
- Log current page URL and hostname

### Deliverables
- Loadable unpacked extension
- Popup with trigger button
- Basic site detection output

### Acceptance Criteria
- Extension loads in Chrome
- User can click popup button
- Extension detects current page URL and hostname

---

## Phase 3: Shared Payload Contract

### Objective
Make the extension and local service speak the same data format.

### Tasks
- Define request schema in local service
- Define response schema in local service
- Build payload formatter in extension
- Implement localhost POST request from extension
- Handle success and failure responses

### Deliverables
- Shared request/response format
- End-to-end localhost communication

### Acceptance Criteria
- Extension can send payload to service
- Service validates request
- Service returns job accepted response
- Extension shows or logs result

---

## Phase 4: Image Downloading

### Objective
Download extracted images locally.

### Tasks
- Implement download service
- Add file naming rules
- Create raw download folders
- Add retry handling
- Add duplicate detection strategy
- Save job metadata

### Deliverables
- Raw image downloader
- Metadata file
- Structured raw folder output

### Acceptance Criteria
- Provided image URLs download successfully
- Files are saved in job folder
- Duplicate downloads are minimized
- Failed downloads are logged clearly

---

## Phase 5: White-Border Trimming

### Objective
Implement first useful image processing step.

### Tasks
- Add crop service
- Implement white or near-white border detection
- Add configurable threshold
- Save cropped outputs to processed folder
- Write tests using sample images

### Deliverables
- Crop service
- Processed output folder
- Unit tests for trimming behavior

### Acceptance Criteria
- Images with visible white borders are cropped correctly
- Main subject is preserved
- Processed files are saved separately from raw files

---

## Phase 6: Site Handler System

### Objective
Support multiple website-specific extraction rules cleanly.

### Tasks
- Define base site handler interface
- Implement first site handler
- Implement second site handler if needed
- Route site detection to correct handler
- Normalize extracted image list

### Deliverables
- Base handler abstraction
- At least one concrete site handler
- Clean extension extraction flow

### Acceptance Criteria
- New site logic can be added without rewriting main extraction flow
- At least one target website works end to end

---

## Phase 7: Stitching and Splitting Pipeline

### Objective
Support scenarios where multiple images form one larger continuous image.

### Tasks
- Implement image ordering logic
- Implement vertical stitch service
- Save stitched result
- Implement basic white-space-based splitting
- Save split outputs
- Add tests with sample sequential images

### Deliverables
- Stitch service
- Split service
- Pipeline orchestration for optional steps

### Acceptance Criteria
- Sequential image sets can be stitched
- Stitched outputs can be split based on white gaps
- Results are saved in dedicated folders

---

## Phase 8: Reliability, Logging, and Storage Refinement

### Objective
Improve maintainability and debugging quality.

### Tasks
- Refine job folder naming rules
- Improve metadata output
- Add structured logs
- Improve error responses
- Add more test coverage
- Add config for thresholds and output roots

### Deliverables
- Better logs
- Better folder structure
- Configurable settings
- Improved test coverage

### Acceptance Criteria
- Failures are diagnosable from logs
- Output folders are consistent
- Thresholds can be tuned without changing code

---

## 4. Suggested Milestone Order for Codex
When using Codex, assign tasks in this order:

1. Create local service skeleton
2. Create extension skeleton
3. Define shared payload schema
4. Connect extension to localhost API
5. Implement image download flow
6. Implement white-border trim
7. Add first site handler
8. Add second site handler or handler abstraction improvements
9. Implement stitching
10. Implement splitting
11. Improve logs and configuration
12. Add tests and clean-up

---

## 5. Testing Plan by Phase

### Phase 1
- Start service
- Check `/health`

### Phase 2
- Load extension manually
- Verify popup trigger works

### Phase 3
- Send sample payload from extension to service
- Verify response parsing

### Phase 4
- Use known image URLs
- Check file output and retry behavior

### Phase 5
- Test trimming on images with white borders
- Test no-overcrop on normal images

### Phase 6
- Test multiple website handlers independently

### Phase 7
- Test sequential image stitching on known sample set
- Test splitting on stitched image with white separators

### Phase 8
- Review logs for successful and failed jobs
- Verify config overrides work

---

## 6. Risks and Mitigation

## Risk 1: Different websites expose image sources differently
### Mitigation
Use a site-handler system and do not assume a single extraction strategy.

## Risk 2: Extracted images may include thumbnails or duplicates
### Mitigation
Add normalization, filtering, and de-duplication rules.

## Risk 3: White borders may not be pure white
### Mitigation
Use adjustable thresholds and preserve margins conservatively.

## Risk 4: Not all image groups should be stitched
### Mitigation
Make stitching optional and rule-driven.

## Risk 5: Browser-localhost communication issues
### Mitigation
Keep the local API simple and define clear CORS and localhost permissions early.

---

## 7. Definition of MVP Done
The MVP is complete when:
- a supported product page can be opened in Chrome
- the extension can extract image URLs
- the extension can send a payload to the local service
- the local service can download the images
- the local service can crop white borders
- the outputs are stored in a structured local folder
- the workflow is documented clearly enough for future expansion
