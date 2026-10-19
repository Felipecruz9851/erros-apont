<!--
SYNC IMPACT REPORT
- Version Change: 1.0.0 → 1.1.0
- Modified Principles:
  - Principle I (Modular Pipeline & Decoupled Data Flow): Expanded to formalize the 6 end-to-end sequential pipeline stages (Login Trigger & Task Generation, Data Extraction, Data Cleaning/Tratamento, Analysis & Calculation, JSON Output Assembly, and Frontend Presentation).
  - Principle II (Isolated & Authenticated Asynchronous Workers): Clarified credential consumption by the Task Generator to instantiate worker authentication contexts safely.
  - Principle V (Standardized DataFrame Dictionary & Output JSON Assembly): Expanded to include intermediate data treatment (cleaning/normalization) and final DataFrame-to-JSON serialization contract.
- Added Sections: None
- Removed Sections: None
- Follow-up TODOs: None
-->

# Erros-apont Constitution

## Core Principles

### I. Modular Pipeline & Decoupled Data Flow
The system MUST follow an end-to-end decoupled, sequential pipeline architecture triggered by user authentication:
1. **Trigger & Task Generation (Login Ingestion)**: The user provides Intranet credentials (login and password) on the frontend. The Task Generator consumes these credentials alongside predefined task skeletons (`url`, `name`, `group`, `payload`, `method`) to parameterize and trigger execution.
2. **Data Extraction (Scraping)**: Asynchronous parallel workers authenticate against the intranet with isolated sessions, fetch raw HTML snapshots, and extract legacy tables via BeautifulSoup.
3. **Data Cleaning & Treatment (Tratamento de Dados)**: Raw tables are cleansed, sanitized, typed, normalized, and consolidated per `group`.
4. **Analysis & Calculation (Análise e Cálculo)**: Pure computational pandas engine executes business rules, identifies pointing errors (*erros de apontamento*), and calculates performance/operational indicators.
5. **Output DataFrame Assembly & JSON Serialization (Montagem do DataFrame em JSON)**: Consolidated analytics results are structured into final output DataFrames and serialized into a standardized, web-ready JSON payload.
6. **API Exposure & Frontend Presentation**: FastAPI serves endpoints for frontend polling or streaming (SSE/WebSocket) to render the resulting reports and dashboards.
Modules MUST respect strict boundary isolation: workers do not clean or calculate business data; the calculation engine performs no network operations.

### II. Isolated & Authenticated Asynchronous Workers
Extraction tasks MUST execute in parallel using asynchronous workers. The Task Generator provisions each worker with authentication parameters so each worker authenticates independently against the intranet, retains its own session token, and operates without cross-worker state interference. User intranet credentials MUST exist only in ephemeral memory and MUST NEVER be written to disk, logged in plaintext, or returned in API responses.

### III. Raw HTML Snapshotting & Auditability
Workers MUST capture and store the complete raw HTML payload of every scraped page before parsing. Full HTML snapshots guarantee an immutable audit record, facilitate deterministic offline debugging, and allow reparsing and verification without redundant requests to internal systems.

### IV. Resilient Legacy Table Parsing (BeautifulSoup)
Extraction of table data from legacy intranet markup MUST use BeautifulSoup and implement robust heuristic pattern recognition. Parsers MUST handle vintage HTML quirks (e.g., unclosed tags, nested presentation tables, non-standard attributes, uppercase tags, complex `colspan`/`rowspan` arrangements) rather than relying on fragile, rigid CSS selectors.

### V. Standardized DataFrame Dictionary, Group Aggregation & JSON Output Assembly
The extraction layer MUST produce data strictly typed and formatted as a dictionary of pandas DataFrames (`Dict[str, pd.DataFrame]`). The pipeline MUST perform systematic data treatment (cleaning, whitespace trimming, column normalization, type coercion) and group-based aggregation. The final analytical result MUST be assembled into an output DataFrame and serialized into a clean JSON structure optimized for frontend visualization.

## Architecture & Technical Constraints

### 1. Technology Stack
- **Language**: Python 3.10+
- **Backend & Web**: FastAPI, Pydantic (data schemas, authentication models, and task contracts), Uvicorn
- **Scraping & Networking**: `requests` / `httpx` with session pooling and async worker management
- **Parsing**: `beautifulsoup4` (with `lxml` / `html.parser` fallback)
- **Data Engine**: `pandas` and `numpy` for data manipulation, cleaning, calculation, and JSON serialization

### 2. Task Skeleton & Ingestion Contract
The task generator MUST consume user login credentials and produce well-defined task configurations supporting manual or programmatically supplied parameters:
- `name`: Unique task identifier
- `group`: Functional aggregation key for grouping multiple tables
- `url`: Target intranet URL
- `method`: HTTP verb (`GET`, `POST`, etc.)
- `payload`: Query parameters, form-data, or JSON payload
- `headers`: Custom headers required for intranet navigation
- `auth_context`: Ephemeral worker credentials/session directive

## Security & Credential Governance

- **Zero Disk Persistence for Passwords**: User credentials provided at the FastAPI login screen are consumed by the task generator and workers exclusively to initialize authentication sessions in memory.
- **Worker Token Expiration**: Authentication tokens must have automated refresh or expiration handling to avoid silent extraction failures.
- **Sanitized Logging**: Network and application logs MUST redact credentials, tokens, and sensitive intranet employee data.

## Quality Gates & Testing Standards

- **Contract Tests**: The dictionary of DataFrames contract between extraction, treatment, calculation, and JSON output layers MUST be enforced with unit and schema validation tests.
- **Fixture-Based Offline Testing**: Unit tests for table parsing MUST run against offline raw HTML fixtures representing historical intranet edge cases.
- **Deterministic Calculations**: The calculation engine MUST be covered by unit tests validating expected numerical and analytical outputs against predefined pandas DataFrames.
- **Clean Architecture & Modularity**: Separation of concerns between network I/O, HTML parsing, pandas treatment, business calculation, JSON serialization, and HTTP presentation is mandatory.

## Governance

This Constitution establishes the foundational architecture and engineering standards for `Erros-apont`. All feature specifications (`spec.md`), implementation plans (`plan.md`), and task breakdowns (`tasks.md`) MUST conform to these principles.
- Amendments require updating this document with an updated version number and amendment record.
- Semantic Versioning is strictly enforced: MAJOR for architectural redesigns or principle removals, MINOR for new principles or core capabilities, PATCH for clarifications.

**Version**: 1.1.0 | **Ratified**: 2026-10-19 | **Last Amended**: 2026-10-19
