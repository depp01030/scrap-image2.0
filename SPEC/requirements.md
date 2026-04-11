# Requirements Specification

## 1. Introduction
This document defines the functional and non-functional requirements for the Local E-commerce Image Collector project.

The system consists of:
- a Chrome extension used locally
- a local service used for image download and processing

---

## 2. Functional Requirements

## 2.1 Chrome Extension

### FR-EXT-001: Site detection
The extension shall detect the current website based on page URL, hostname, or other page metadata.

### FR-EXT-002: Supported site matching
The extension shall determine whether the current page belongs to a supported site.

### FR-EXT-003: Site handler selection
The extension shall route page extraction logic to a site-specific handler.

### FR-EXT-004: Product page image extraction
The extension shall extract product image URLs from supported product pages.

### FR-EXT-005: Multi-strategy extraction
The extension should support multiple extraction strategies, including but not limited to:
- DOM image elements
- lazy-load attributes
- srcset values
- inline JSON/script data
- page source patterns
- site-specific logic

### FR-EXT-006: Data normalization
The extension shall normalize extracted data into a standard payload schema before sending it to the local service.

### FR-EXT-007: Local service communication
The extension shall send the standardized payload to the local service through a localhost HTTP API.

### FR-EXT-008: Basic response handling
The extension shall display or log whether the local service accepted or rejected the request.

### FR-EXT-009: Page interaction compatibility
The extension should tolerate websites that interfere with normal page interaction or content inspection, as long as the content is already visible to the user in the browser.

### FR-EXT-010: Manual trigger
The extension should support at least one manual trigger mechanism, such as:
- popup button
- context action
- browser action button

---

## 2.2 Local Service

### FR-SVC-001: Request reception
The local service shall expose a local HTTP API endpoint for receiving extraction payloads from the extension.

### FR-SVC-002: Payload validation
The local service shall validate incoming payload structure and reject malformed requests.

### FR-SVC-003: Job creation
The local service shall create a processing job for each accepted request.

### FR-SVC-004: Image downloading
The local service shall download images from the provided URL list.

### FR-SVC-005: Download retry
The local service should retry failed downloads a configurable number of times.

### FR-SVC-006: Duplicate avoidance
The local service should avoid unnecessary repeated downloads for identical image sources when possible.

### FR-SVC-007: Raw image storage
The local service shall save original downloaded images in a raw folder.

### FR-SVC-008: Image processing pipeline
The local service shall process images through a configurable processing pipeline.

### FR-SVC-009: White-border trimming
The local service shall support detection and removal of white or near-white image borders.

### FR-SVC-010: Sequential image stitching
The local service should support stitching multiple images into a larger image when the images are determined to be consecutive segments of one larger image.

### FR-SVC-011: Content-based splitting
The local service should support splitting stitched images based on white-space boundaries or content boundaries.

### FR-SVC-012: Processed image output
The local service shall save processed images into designated output folders.

### FR-SVC-013: Metadata recording
The local service shall store metadata for each processing job, including at minimum:
- page URL
- site code
- job identifier
- image URL list
- timestamps
- output folder path

### FR-SVC-014: Logging
The local service shall produce logs for request handling, downloading, image processing, and storage outcomes.

### FR-SVC-015: Error reporting
The local service shall return structured error responses for failed requests.

---

## 3. Payload Requirements

### FR-DATA-001: Standard request schema
The request payload should include:
- site_code
- page_url
- product_id (optional)
- product_name (optional)
- image_urls
- metadata

### FR-DATA-002: Standard response schema
The local service response should include:
- success
- job_id (if accepted)
- message
- error details (if failed)

---

## 4. Image Processing Requirements

## 4.1 White-border trimming
The system shall support trimming of white or near-white borders.

### Processing expectations
- Detect border regions from all four sides
- Use configurable threshold values
- Preserve the main content region
- Avoid over-cropping the product itself

## 4.2 Image stitching
The system should support combining multiple images if they appear to be segments of one larger continuous image.

### Processing expectations
- Use ordering rules
- Support vertical stitching first
- Allow future overlap detection improvements

## 4.3 Image splitting
The system should support splitting stitched images into separate outputs using white gaps or low-content-density regions.

---

## 5. Storage Requirements

### FR-STO-001: Structured output folders
The system shall save data into a structured folder hierarchy.

### FR-STO-002: Separation of raw and processed outputs
The system shall separate:
- raw downloads
- processed outputs
- stitched outputs
- split outputs
- metadata files

### FR-STO-003: Predictable naming
The system should use consistent naming rules for folders and files.

---

## 6. Non-Functional Requirements

### NFR-001: Local-only execution
The entire system shall run locally without cloud dependency.

### NFR-002: Extensibility
The system shall support addition of new site handlers with minimal changes to the main flow.

### NFR-003: Maintainability
The system shall use modular code organization with clear responsibility boundaries.

### NFR-004: Observability
The system shall provide sufficient logging for debugging extraction and processing failures.

### NFR-005: Testability
The system should allow unit testing for:
- site handler logic
- payload validation
- image trimming
- image stitching
- image splitting

### NFR-006: Configurability
The system should allow configuration of:
- local service port
- output root path
- retry count
- image thresholds
- supported site settings

### NFR-007: Reliability
The system should fail gracefully and preserve logs and partial outputs when possible.

### NFR-008: Performance
For MVP, performance should be sufficient for single-job local usage rather than high concurrency.

---

## 7. Constraints

### CON-001
The Chrome extension is for local/private use only.

### CON-002
The local service runs only on localhost.

### CON-003
The system should not depend on a database in the initial MVP.

### CON-004
The initial implementation should prioritize readability and extensibility over premature optimization.

---

## 8. Assumptions

### ASM-001
The user manually opens supported product pages in Chrome.

### ASM-002
The user can run a local Python service.

### ASM-003
The initial number of supported websites is small.

### ASM-004
Image processing rules may vary across websites and product types, so heuristics may need later refinement.

---

## 9. Out of Scope for MVP
- Authentication
- Cloud synchronization
- Distributed processing
- Browser store publication
- General-purpose scraping of arbitrary websites
- Fully automated crawling across many pages
