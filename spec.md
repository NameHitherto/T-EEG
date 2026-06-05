# T-EEG Technical Architecture Specification

Last updated: 2026-06-05

## 1. Project Positioning

T-EEG is an EEG research and application project. The codebase is organized as a two-part system:

- `eeg`: Python-based EEG core implementation, including data processing, analysis algorithms, model training/inference, service APIs, and research utilities.
- `webui`: Vue 3 web interface for visualization, user interaction, experiment operation, and result inspection.

The architecture should support both research iteration and eventual production service development. Research code must be reproducible, dependency-locked, testable, and separable from user-facing web interaction.

## 2. Top-Level Repository Layout

```text
T-EEG/
  spec.md
  eeg/
    pyproject.toml
    uv.lock
    .python-version
    README.md
    src/
      teebg/
        __init__.py
        config/
        data/
        preprocessing/
        features/
        models/
        pipelines/
        services/
        utils/
    tests/
    scripts/
    notebooks/
    data/
      .gitkeep
  webui/
    package.json
    pnpm-lock.yaml
    index.html
    vite.config.ts
    tsconfig.json
    src/
      main.ts
      App.vue
      router/
      stores/
      api/
      layouts/
      views/
      components/
      assets/
      styles/
      types/
    tests/
```

Notes:

- The Python package import name is `teebg` to avoid colliding with generic `eeg` names in local variables or third-party packages.
- `eeg/data/` is reserved for local or small fixture data only. Large EEG datasets, raw subject data, generated models, and experiment outputs must not be committed to Git.
- Shared documentation can live at the repository root. Python-specific docs belong in `eeg/README.md`; frontend-specific docs belong in `webui/README.md`.

## 3. Python Core Standard

### 3.1 Language And Package Manager

- Python version: pin with `eeg/.python-version`. Default target: Python `3.12`, unless a required EEG library does not support it.
- Package manager: `uv`.
- Dependency metadata: `eeg/pyproject.toml`.
- Lock file: `eeg/uv.lock`, committed to Git.

Rationale: `uv` provides fast dependency resolution, project management, Python version management, virtual environments, and a universal lock file in one tool. It is a good fit for research projects where environments must be recreated reliably across machines.

Standard commands:

```powershell
cd eeg
uv sync
uv add <package>
uv add --dev <package>
uv run python -m pytest
uv run ruff check .
uv run ruff format .
```

### 3.2 Core Dependencies

Initial Python dependency categories:

- Numerical computing: `numpy`, `scipy`, `pandas`.
- EEG and signal processing: `mne`.
- Machine learning baseline: `scikit-learn`.
- Configuration and validation: `pydantic`, `pydantic-settings`.
- API service, when needed: `fastapi`, `uvicorn`.
- Testing and quality: `pytest`, `pytest-cov`, `ruff`, `mypy`.

Deep learning dependencies such as `torch`, `pytorch-lightning`, or GPU-specific libraries should be added only when a concrete modeling task requires them, because they significantly affect installation size, CUDA compatibility, and reproducibility.

### 3.3 Python Module Boundaries

`teebg.data`
: Loading, saving, dataset indexing, metadata parsing, and file format adapters.

`teebg.preprocessing`
: Filtering, referencing, artifact handling, epoching, normalization, and other signal preparation logic.

`teebg.features`
: Feature extraction, time-frequency transforms, band power, connectivity metrics, and derived EEG representations.

`teebg.models`
: Model definitions, training adapters, evaluation utilities, and inference wrappers.

`teebg.pipelines`
: End-to-end workflows that compose data loading, preprocessing, feature extraction, modeling, and report generation.

`teebg.services`
: Service-facing APIs such as FastAPI routers, request/response schemas, and application factories.

`teebg.config`
: Typed configuration, environment variable mapping, and path settings.

`teebg.utils`
: Small generic helpers only. Domain logic should stay in domain modules, not in `utils`.

### 3.4 Research Code Rules

- Reusable logic belongs under `src/teebg/`.
- One-off experiment scripts belong under `scripts/`.
- Exploratory notebooks belong under `notebooks/`.
- A notebook may demonstrate or inspect results, but it must not be the only place where a core algorithm exists.
- Pipelines should be callable from Python code and optionally wrapped by scripts or services.
- Random seeds, data split strategy, preprocessing parameters, and model parameters must be explicit and recorded.

### 3.5 Data And Artifact Policy

Do not commit:

- Raw EEG datasets.
- Subject-identifying data.
- Large intermediate arrays.
- Trained model binaries.
- Generated reports or experiment output folders, unless they are tiny fixtures for tests.

Recommended local directories:

```text
eeg/data/raw/
eeg/data/processed/
eeg/data/fixtures/
eeg/artifacts/
eeg/runs/
```

Only `eeg/data/fixtures/` may contain small committed test data. All other data/artifact directories should be ignored by Git.

### 3.6 Python Quality Standard

- Formatting and linting: `ruff`.
- Type checking: `mypy` for stable modules and service boundaries.
- Tests: `pytest`.
- Minimum test expectation:
  - Unit tests for preprocessing and feature extraction.
  - Fixture-based tests for data loaders.
  - Regression tests for pipeline outputs when algorithms stabilize.
  - API tests when service endpoints are introduced.

Core EEG processing functions should avoid hidden global state. Prefer typed function inputs, explicit configuration objects, and deterministic outputs.

## 4. WebUI Standard

### 4.1 Frontend Stack

- Framework: Vue 3.
- Language: TypeScript.
- Build tool: Vite.
- Package manager: `pnpm`.
- UI component library: Element Plus.
- Router: Vue Router.
- State management: Pinia.
- HTTP client: Axios or a small Fetch wrapper. Choose one and centralize it under `src/api/`.

Standard commands:

```powershell
cd webui
pnpm install
pnpm dev
pnpm build
pnpm test
pnpm lint
```

### 4.2 Frontend Source Layout

`src/main.ts`
: Application bootstrap only. Register Vue app, router, store, Element Plus, global styles, and mount.

`src/App.vue`
: Root shell only. It should define the application frame and route outlet, not feature-specific business UI.

`src/layouts/`
: Layout shells such as main app layout, analysis workspace layout, or auth layout.

`src/views/`
: Route-level view components. Views compose reusable components and connect to stores/API calls.

`src/components/`
: Reusable presentational or interaction components. Components should be domain-named when they are EEG-specific.

`src/api/`
: API clients, endpoint modules, request/response mapping, and transport configuration.

`src/stores/`
: Pinia stores for cross-view state. Avoid putting one-component local state here.

`src/types/`
: Shared TypeScript types, DTOs, and domain models.

`src/styles/`
: Global styles, Element Plus overrides, design tokens, and reset/base CSS.

### 4.3 Frontend Component Rules

- `App.vue` and route views define structure; reusable widgets live in `components`.
- Keep view components responsible for orchestration, not detailed rendering logic.
- Keep API response types separate from UI view models when transformation is needed.
- Element Plus components are the default for forms, tables, dialogs, menus, tabs, notifications, and layout primitives.
- Use TypeScript `strict` mode.
- Prefer `script setup` single-file components.
- Avoid hard-coded API URLs in components. Use environment variables and a central API client.

### 4.4 WebUI Quality Standard

- Unit tests: Vitest.
- Component tests: Vue Test Utils.
- End-to-end tests: Playwright when critical user workflows exist.
- Linting: ESLint.
- Formatting: Prettier, or ESLint formatting if the project standardizes on it.
- Build must pass `pnpm build` before merging substantial UI changes.

## 5. Backend-Service Boundary

When the web interface needs live Python capabilities, expose them from `eeg/src/teebg/services/` rather than importing Python logic into frontend tooling.

Recommended service structure:

```text
eeg/src/teebg/services/
  api/
    app.py
    routes/
    schemas/
  workers/
  dependencies.py
```

API rules:

- Use FastAPI for HTTP APIs when a backend is needed.
- Keep API schemas typed with Pydantic.
- API responses should be frontend-friendly and stable.
- Long-running EEG jobs should be modeled as asynchronous jobs with status polling or streaming, not blocking requests.
- The web UI communicates with backend services through `webui/src/api/` only.

## 6. Cross-Project Contracts

Shared contracts between Python and WebUI must be explicit:

- REST endpoints documented in OpenAPI generated by FastAPI.
- Frontend DTOs generated from OpenAPI when the API surface becomes large, or manually maintained under `webui/src/types/` for small early-stage APIs.
- EEG result payloads should use JSON-compatible structures for metadata and lightweight arrays.
- Large signal arrays should be transferred through files, object storage, or chunked/streamed endpoints rather than giant JSON payloads.

## 7. Environment Configuration

Python:

- Use `.env` for local development overrides.
- Use `pydantic-settings` to load typed settings.
- Keep secrets out of source control.

WebUI:

- Use Vite environment variables with the `VITE_` prefix.
- Example: `VITE_API_BASE_URL=http://localhost:8000`.
- Environment-specific files may exist locally, but secrets must not be committed.

## 8. Git And Generated Files

The repository should ignore:

- Python virtual environments: `.venv/`.
- Python caches: `__pycache__/`, `.pytest_cache/`, `.ruff_cache/`, `.mypy_cache/`.
- Frontend dependencies and build output: `node_modules/`, `dist/`.
- EEG data/artifacts: `eeg/data/raw/`, `eeg/data/processed/`, `eeg/artifacts/`, `eeg/runs/`.
- Editor and OS noise.

Commit lock files:

- `eeg/uv.lock`
- `webui/pnpm-lock.yaml`

## 9. Recommended Initial Bootstrap

Python:

```powershell
cd eeg
uv init --package --name teebg
uv python pin 3.12
uv add numpy scipy pandas mne scikit-learn pydantic pydantic-settings
uv add --dev pytest pytest-cov ruff mypy
```

WebUI:

```powershell
cd webui
pnpm create vite . --template vue-ts
pnpm add element-plus @element-plus/icons-vue vue-router pinia axios
pnpm add -D vitest @vue/test-utils eslint prettier typescript
```

Service dependencies, when required:

```powershell
cd eeg
uv add fastapi uvicorn
```

## 10. Architecture Decisions

1. Python package manager is `uv`.
2. Python project uses `pyproject.toml` and committed `uv.lock`.
3. Python source uses `src/teebg/` package layout.
4. EEG domain logic lives in Python; WebUI only consumes service/API contracts.
5. WebUI package manager is `pnpm`.
6. WebUI framework stack is Vue 3 + TypeScript + Vite + Element Plus.
7. `main.ts` and `App.vue` remain bootstrap/shell files; feature UI belongs in `views` and `components`.
8. Large datasets, artifacts, trained models, and experiment outputs are not committed.
9. FastAPI is the standard backend service framework once HTTP service capabilities are needed.
10. Both Python and WebUI must keep lock files committed for reproducible development.
