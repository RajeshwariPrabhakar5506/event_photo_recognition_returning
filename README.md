# Technical Architecture Document: Event Face Finder

This document provides the formal architectural blueprint of the **Event Face Finder** platform. It details the system's multi-tiered design, micro-process execution lifecycle, hardware utilization, data storage topologies, and biometric pipeline mechanics.

---

## 1. High-Level Architectural Pattern

The platform uses a **Hybrid-Edge Decoupled Architecture**. 

* **The Edge (Local Machine):** Heavy, compute-intensive biometric inference (vector transformations, ResNet feature projections, Euclidean distance matrix multiplications) runs locally on host hardware. This eliminates GPU compute fees and cloud infrastructure costs.
* **The Cloud Boundary:** External services are accessed strictly for data ingestion (Google Forms, Google Sheets, Google Drive API) and transactional dispatch (SMTP relay networks). Biometrics never leave the local machine.

```
 +-------------------------------------------------------------------------+
 |                            CLIENT TIER                                  |
 |   Modern Web Browser (Desktop / Tablet / Smartphone on Local LAN)       |
 +------------------------------------+------------------------------------+
                                      |
                         HTTP REST / JSON (Port 5000)
                                      |
 +------------------------------------v------------------------------------+
 |                       APPLICATION / GATEWAY TIER                        |
 |   Flask Web Server (app.py) & Non-Blocking Subprocess Orchestrator      |
 +---------+-----------------+-------------------+-----------------+-------+
           |                 |                   |                 |
     (1) Ingest        (2) Index           (3) Match         (4) Dispatch
           |                 |                   |                 |
 +---------v------+  +-------v--------+  +-------v--------+  +-----v-------+
 | index_faces.py |  | create_index.py|  |find_matches.py |  |send_emails  |
 +---------+------+  +-------+--------+  +-------+--------+  +-----+-------+
           |                 |                   |                 |
           v                 v                   v                 v
   [Google Cloud]      [encodings.pkl]     [results.json]     [SMTP Server]
   Drive / Sheets       (128D Matrix)      (Match Ledger)     (TLS Port 587)
```

---

## 2. Four-Tier Architectural Decomposition

### Tier 1: Presentation & Client Interface (`templates/index.html`)
* **Role:** Single-page administrative cockpit.
* **Tech Stack:** HTML5, CSS3, Bootstrap 5.3, Bootstrap Icons, Native JavaScript (Fetch API).
* **Key Components:**
  * **Asynchronous Action Controllers:** Buttons that send non-blocking `POST` requests to backend endpoints (`/sync-users`, `/upload-photos`, `/run-matching`, `/send-emails`).
  * **Visual State Machine:** Replaces loading text with animated Bootstrap spinners and temporarily locks out concurrent operations.
  * **Two-Phase Commit Email Safety Switch:** A hardware-style toggle switch preventing accidental activation of the SMTP dispatcher before manual inspection of match counts.
  * **Realtime Terminal Stream:** A scrollable telemetry console capturing `STDOUT` and `STDERR` streams from background Python processes.

---

### Tier 2: Application Controller & Orchestration Tier (`app.py`)
* **Role:** API Gateway, task supervisor, security sanitizer, and static asset host.
* **Tech Stack:** Python 3, Flask, Werkzeug.
* **Core Responsibilities:**
  * **REST Routing:** Maps client actions to discrete system tasks.
  * **Payload Sanitization:** Uses Werkzeug's `secure_filename` to prevent path traversal attacks (e.g., preventing inputs like `../../system32`).
  * **Subprocess Supervision:** Uses Python's `subprocess.run()` to execute AI scripts in isolated execution spaces with dedicated memory bounds. If an AI script encounters an issue, the Flask server remains online.

```
       [ Client POST: /run-matching ]
                     |
                     v
         [ Flask Route Controller ]
                     |
       +-------------+-------------+
       | Spawns Child Subprocess   | --> Executes: sys.executable find_matches.py
       +-------------+-------------+
                     |
       +-------------+-------------+
       | Intercepts I/O Buffers    | <-- Captures stdout & stderr
       +-------------+-------------+
                     |
       +-------------+-------------+
       | Returns JSON Envelope     | --> { status: "success", matches: {...}, output: "..." }
       +---------------------------+
```

---

### Tier 3: Computational Vision & Micro-Execution Tier
This tier consists of four modular Python micro-scripts:

```
+------------------+------------------------------------------------------------------+
| Script           | Architectural Functionality                                      |
+------------------+------------------------------------------------------------------+
| index_faces.py   | OAuth2 cloud ingress; streams images from Google Drive API.      |
| create_index.py  | Compiles raw biometric pixels into 128D linear embeddings.       |
| find_matches.py  | Performs HOG face localization and L2 distance matrix scoring.   |
| send_emails.py   | Assembles multi-part MIME containers and handles SMTP over TLS.  |
+------------------+------------------------------------------------------------------+
```

#### Detailed Vision Execution Pipeline (`find_matches.py`):
For every uploaded image, the engine processes data across three distinct sub-layers:

$$\text{Raw Event Photo} \xrightarrow{\text{Stage 1}} \text{Bounding Box} \xrightarrow{\text{Stage 2}} \mathbf{x} \in \mathbb{R}^{128} \xrightarrow{\text{Stage 3}} \text{L2 Norm Comparison}$$

1. **Detection Stage (HOG + Linear SVM):**
   * Converts the image to grayscale.
   * Computes directional gradient histograms across localized $8 \times 8$ pixel blocks.
   * Evaluates shapes against a linear Support Vector Machine to locate bounding coordinates $[t, r, b, l]$.

2. **Embedding Projection Stage (Deep ResNet-34):**
   * Uses a 68-point facial landmark predictor to warp and affine-align the face (aligning eye corners, nose tip, and lip contours).
   * Passes the aligned crop through a pre-trained 29-layer residual neural network.
   * Outputs a normalized 128-dimensional floating-point vector $\mathbf{p}$.

3. **Metric Classification Stage:**
   * Computes the Euclidean Distance against all known indexed attendee embeddings $\mathbf{q}$:
     $$d(\mathbf{p}, \mathbf{q}) = \sqrt{\sum_{i=1}^{128} (p_i - q_i)^2}$$
   * If $d(\mathbf{p}, \mathbf{q}) \le T$ (where $T = 0.6$), a positive match is registered.

---

### Tier 4: Storage & Data Persistence Tier
The architecture uses flat-file, zero-dependency storage to ensure fast local read/write cycles without requiring a standalone database server (like PostgreSQL or MongoDB):

```
face_finder_project/
│
├── encodings.pkl            <-- Serialized Binary Matrix: List[Dict{name, email, ndarray}]
├── results.json             <-- JSON Ledger: Dict{email: {name: str, photos: List[str]}}
│
├── reference_photos/        <-- Target Directory for Known User Face Baselines
│   └── {FullName}_{Email}.jpg
│
└── event_photos/            <-- Batch Gallery Storage for Ingested Event Images
    ├── DSC_0001.jpg
    └── DSC_0002.jpg
```

---

## 3. End-to-End System Sequence Diagram

```
[Attendee]      [Admin UI]       [Flask Server]       [Worker Scripts]     [Cloud / SMTP]
    |               |                  |                     |                    |
    |--Fill Form--->|                  |                     |                    |
    |  (Photo/Info) |                  |                     |                    |
    |               |                  |                     |---Upload to Sheet->|
    |               |                  |                     |   & Google Drive   |
    |               |                  |                     |                    |
    |               |--Sync Users----->|                     |                    |
    |               |                  |--Run index_faces.py>|                    |
    |               |                  |                     |<--Download Photos--|
    |               |                  |--Run create_index-->|                    |
    |               |                  |                     |--Write encodings-->[encodings.pkl]
    |               |<--Sync Finished--|                     |                    |
    |               |                  |                     |                    |
    |               |--Upload Photos-->|                     |                    |
    |               |  (Store local)   |-->Saves ./event_photos                   |
    |               |                  |                     |                    |
    |               |--Find Matches--->|                     |                    |
    |               |                  |--Run find_matches-->|                    |
    |               |                  |                     |<--Read encodings---[encodings.pkl]
    |               |                  |                     |--Write results---->[results.json]
    |               |<--Matches JSON---|                     |                    |
    |               |                  |                     |                    |
    |               |--[Unlock Switch] |                     |                    |
    |               |--Send Emails---->|                     |                    |
    |               |                  |--Run send_emails.py>|                    |
    |               |                  |                     |--Connect TLS------>|
    |               |                  |                     |--Dispatch Attach.->|
    |               |<--Emails Sent----|                     |                    |
```

---

## 4. Hardware Sizing & Scalability Metrics

### Computational Complexity
* **Face Encoding Construction:** $O(K)$, where $K$ is the total count of registered attendees.
* **Match Evaluation:** $O(M \times N \times K)$, where:
  * $M$ = Number of event photos.
  * $N$ = Average faces detected per event photo.
  * $K$ = Number of registered attendees in `encodings.pkl`.

### Memory Footprint
* Each 128-dimensional face embedding consists of 128 64-bit floating-point numbers:
  $$\text{Size per face} = 128 \times 8 \text{ bytes} = 1024 \text{ bytes } (1\text{ KB})$$
* A registration base of **10,000 attendees** requires only $\approx 10\text{ MB}$ of memory, allowing the entire database matrix to reside in RAM during match operations.

---

## 5. Security & Network Perimeter Design

1. **Biometric Anonymization:** Raw attendee photos are converted into 128-dimensional vectors. These projections are mathematically non-invertible: an original facial image cannot be reverse-engineered or reconstructed from its vector coordinates.
2. **Local Processing Boundary:** Images and biometrics remain isolated on the local workstation. No biometric data is sent to external computer vision APIs.
3. **Network Concurrency Control:** Flask binds to `0.0.0.0:5000` to allow access from local mobile devices over Wi-Fi, while keeping the application sandboxed behind local network firewalls.
