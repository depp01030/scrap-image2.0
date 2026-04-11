# Architecture Specification

## 1. Architecture Overview
The system is split into two main components:

1. **Chrome Extension**
2. **Local Service**

This separation keeps browser-specific logic in the extension and file/image-processing logic in the local service.

---

## 2. High-Level Architecture

```text
[User on Product Page]
        ↓
[Chrome Extension]
  - detect site
  - extract image URLs
  - normalize payload
  - send localhost request
        ↓
[Local Service API]
  - validate request
  - create job
        ↓
[Download Layer]
  - fetch image files
        ↓
[Image Processing Pipeline]
  - trim borders
  - optionally stitch
  - optionally split
        ↓
[Storage Layer]
  - save raw
  - save processed
  - save metadata/logs
```

---

## 3. Chrome Extension Architecture

## 3.1 Responsibilities
The extension is responsible for:
- detecting the current site
- choosing the correct extraction handler
- extracting candidate image URLs
- normalizing extracted data
- sending the request to the local service

The extension is not responsible for:
- heavy image processing
- local file storage
- batch image transformation
- long-running task orchestration

---

## 3.2 Recommended Folder Structure

```text
extension/
  manifest.json
  background/
    service-worker.js
  content/
    page-scanner.js
  popup/
    popup.html
    popup.js
  site-handlers/
    base-handler.js
    site-a-handler.js
    site-b-handler.js
  utils/
    dom-utils.js
    url-utils.js
    api-client.js
    payload-builder.js
```

---

## 3.3 Key Extension Modules

### manifest.json
Defines permissions, content scripts, host permissions, and service worker registration.

### content/page-scanner.js
Runs in the page context or content-script context and collects page information.

### popup/popup.js
Provides a manual trigger for extraction and sending.

### site-handlers/base-handler.js
Defines the common interface for site-specific handlers.

### site-handlers/site-a-handler.js
Implements extraction rules for one supported site.

### utils/api-client.js
Sends requests to the local service.

### utils/payload-builder.js
Normalizes data into the shared request schema.

---

## 3.4 Site Handler Interface
Each site handler should expose a predictable contract.

Suggested interface:
- `canHandle(url, document): boolean`
- `extractImages(document): string[]`
- `extractProductInfo(document): object`
- `buildMetadata(): object`

This allows new sites to be added with minimal impact on the main extension flow.

---

## 4. Local Service Architecture

## 4.1 Responsibilities
The local service is responsible for:
- receiving requests from the extension
- validating payloads
- creating processing jobs
- downloading images
- running image-processing steps
- saving outputs and metadata
- logging the workflow

---

## 4.2 Recommended Folder Structure

```text
local_service/
  app/
    main.py
    api/
      routes_jobs.py
    schemas/
      job_request.py
      job_response.py
    services/
      job_service.py
      download_service.py
      image_pipeline_service.py
      crop_service.py
      stitch_service.py
      split_service.py
      storage_service.py
    site_rules/
      site_a_rule.py
      site_b_rule.py
    core/
      config.py
      logger.py
    utils/
      image_utils.py
      hash_utils.py
  output/
  raw_downloads/
  logs/
```

---

## 4.3 Key Local Service Modules

### app/main.py
Application entry point.

### api/routes_jobs.py
Defines the local HTTP API endpoints.

### schemas/job_request.py
Defines the request validation schema.

### schemas/job_response.py
Defines the response model.

### services/job_service.py
Coordinates the full job lifecycle.

### services/download_service.py
Downloads image files and manages retries and de-duplication.

### services/image_pipeline_service.py
Executes image-processing steps in order.

### services/crop_service.py
Implements white-border trimming.

### services/stitch_service.py
Combines sequential images into one image.

### services/split_service.py
Splits a stitched image into multiple outputs.

### services/storage_service.py
Defines folder creation, file writing, and metadata output.

### core/config.py
Loads local configuration such as port, output paths, and thresholds.

### core/logger.py
Configures logging output.

---

## 5. Shared Data Contract

## 5.1 Request Payload Example

```json
{
  "site_code": "site_a",
  "page_url": "https://example.com/product/123",
  "product_id": "123",
  "product_name": "sample product",
  "image_urls": [
    "https://img.example.com/a.jpg",
    "https://img.example.com/b.jpg"
  ],
  "metadata": {
    "captured_at": "2026-04-11T10:00:00+08:00",
    "handler_version": "1.0.0"
  }
}
```

## 5.2 Response Example

```json
{
  "success": true,
  "job_id": "job_20260411_001",
  "message": "job accepted"
}
```

---

## 6. Image Processing Pipeline Design

## 6.1 Pipeline Philosophy
Image processing should be composed of small steps rather than one large monolithic function.

This enables:
- easier testing
- clearer debugging
- optional steps based on site needs
- future expansion

---

## 6.2 Suggested Pipeline

```text
1. Validate job input
2. Create output folders
3. Download raw images
4. Sort or normalize image order
5. Apply white-border trimming to individual images
6. Decide whether stitching is needed
7. Stitch images if needed
8. Analyze stitched result
9. Split stitched image if needed
10. Save outputs and metadata
11. Write job logs
```

---

## 6.3 Pipeline Components

### Crop Service
Input:
- single image

Output:
- cropped image

Purpose:
- remove white or near-white borders

### Stitch Service
Input:
- ordered image list

Output:
- one combined image

Purpose:
- reconstruct one continuous image from several partial segments

### Split Service
Input:
- stitched image

Output:
- multiple segmented images

Purpose:
- split a larger image into cleaner parts based on white-space or content boundaries

---

## 7. Storage Architecture

## 7.1 Example Output Layout

```text
output/
  site_a/
    20260411_123456_product123/
      metadata.json
      raw/
        001.jpg
        002.jpg
      processed/
        001_cropped.jpg
        002_cropped.jpg
      stitched/
        merged.jpg
      split/
        part_001.jpg
        part_002.jpg
```

---

## 7.2 Storage Principles
- Preserve raw downloads
- Keep processed outputs separate
- Save metadata alongside image outputs
- Use predictable paths
- Make manual review easy

---

## 8. Logging and Error Strategy

## 8.1 Logging
Each job should log:
- request receipt
- payload validation result
- download start/end/failure
- processing step result
- storage result
- final job status

## 8.2 Error Handling
The system should:
- reject malformed payloads early
- keep partial logs
- preserve raw downloads when useful
- return structured error messages

---

## 9. Future Architecture Extensions
The architecture should allow future support for:
- more site handlers
- job queueing
- richer popup UI
- batch processing
- per-site processing rules
- local history viewer
- configuration UI
