# PixelMotion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver a standalone local PixelMotion repository that generates or imports media, preserves an editable project, supports footage/caption/audio/motion changes, and exports those saved decisions.

**Architecture:** Curated commit-pinned MoneyPrinterTurbo and Herk engines run behind isolated adapters. A FastAPI control service owns immutable assets, canonical project revisions and durable jobs; one React studio edits that project. The saved revision compiles to one HyperFrames/native-animation export path.

**Tech Stack:** Python 3.11, FastAPI, SQLite, JSON Schema, Node >=22, React/TypeScript, Shadcn, Vite, HyperFrames 0.7.109, native WAAPI, FFmpeg/FFprobe, pytest, Vitest and Testing Library.

**Spec:** [2026-10-28-pixelmotion-design.md](../specs/2026-10-28-pixelmotion-design.md). The user approved the written spec by requesting implementation. This plan still requires review and an execution-method selection; no product scaffolding is performed by writing it.

## Global Constraints

- Implementation destination: `/home/micxsz/projects/pixelmotion`; initialize a separate Git repository on `codex/pixelmotion-initial`. Never write to protected `/home/bomiku1/projects/dineEase-web` or change PixelCore application code.
- Product identity: **PixelMotion — All-in-one creative video editor.** First usable workflow: **generate → edit → animate → export**.
- “The first release is a single-user, local-first application with a browser studio and supervised local media workers.”
- “The first release supports projects up to 10 minutes and 100 video clips, with portrait 1080×1920, landscape 1920×1080 and square 1080×1080 canvases. Export rates are 30 or 60 fps, default 30.”
- “Playback speed is fixed at 1× initially. Video scenes use hard cuts.”
- `schema_version=1`; `ticks_per_second=240000`; frame boundaries are 8,000 ticks at 30 fps and 4,000 at 60 fps; half-open intervals and safe integer times.
- Herk commit `10511e5af86fc47756ea89803b397422e2d89284`; MoneyPrinter commit `dd5ee71a0fbbb2c06401a7a4401bc83830a7c4d1`; HyperFrames `0.7.109`. Other dependencies receive exact resolved lockfiles at execution.
- Retain upstream notices, hashes and patches. Exclude AIS assets, uncleared songs/fonts, nested Git directories, upstream agent instructions, secrets, caches and generated output.
- Default studio motion uses three native presets: title, lower third and callout. Keep GSAP outside that path; do not advertise all draft cards as supported.
- Offline preparation makes no network/model-download calls. Connected mode supports explicit script generation, Pexels footage, Edge TTS or supplied narration and optional captions. No automatic publishing.
- One durable local media slot. Heartbeat every five seconds; lease 30 seconds; cancellation grace five seconds; generation/export attempt deadline 30 minutes; preparation/probe stage deadline 10 minutes.
- “The canonical JSON document is the editing source of truth”; no alternative legacy final-video exporter for edited projects.
- “Errors use `{error:{code,message,item_ids,retryable}}`.” Credentials never enter public documents, receipts, logs or browser responses.
- Automated checks by default; no frontend/backend builds, visual tests, browser-based visual inspections or manual verification unless the user explicitly requests them. Media rendering plus metadata/state assertions are functional output checks, not visual approval.

## Review Focus

1. Supplied script without search terms could invoke an undisclosed default LLM: reject admission without explicit terms or a selected LLM (Task 4).
2. A worker can finish during cancellation or after its revision becomes stale: transactional promotion must preserve cancellation and the current head (Tasks 3 and 7).
3. Herk drops retained segments shorter than 0.04 seconds and rounds times to milliseconds: preserve a complete 30/60 fps frame and original provenance in the canonical map (Task 5).
4. Native animations use global time and can remain visible through `fill: both`: test delayed entry, slot exit and repeated seeking after reorder (Task 6).
5. Imported SRT may contain CRLF, UTF-8 BOM, overlaps or invalid cue bounds: normalize encoding/line endings, retain genuine overlaps on distinct cue items, reject invalid bounds, and never invent word alignment (Tasks 2 and 4).

## File and contract map

All paths below are relative to the new repository. Copy this plan, the approved spec and `docs/pixelmotion/REPOSITORY-ANALYSIS.md` into matching documentation locations there. Keep original source citations intact.

| Unit | Files / responsibility |
| --- | --- |
| Repository/runtime | `package.json`, `package-lock.json`, `.gitignore`, `AGENTS.md`, `README.md`, `scripts/{setup,dev,doctor,vendor}.mjs`, `vendor-manifest.json`, `patches/` |
| Canonical contract | `packages/project-schema/{package.json,project.schema.json,generation.schema.json,fixtures/,scripts/generate-types.mjs,src/generated.ts}` |
| Control API | `apps/api/{pyproject.toml,uv.lock,src/pixelmotion/,tests/}`; modules named in tasks below |
| MoneyPrinter bridge | `adapters/moneyprinter/{pyproject.toml,src/pixelmotion_moneyprinter/{command,config,result}.py}`; a standard-library bridge installed into the API environment, never importing upstream `app.*` |
| Herk bridge | `adapters/herk/{package.json,src/{propose,validate}.mjs,tests/}`; subprocess wrappers and explicit policy adaptations |
| Renderer | `packages/render-runtime/{package.json,src/{compile,motion,validate,cli}.mjs,templates/,tests/}` |
| Studio | `apps/studio/{package.json,tsconfig.json,vite.config.ts,src/,scripts/check-ui.mjs}`; shared UI in `src/components/ui/` |
| Engine code | `engines/{herk,moneyprinter}/` with curated original paths and applied recorded patches |
| Private local data | `.pixelmotion/` ignored: SQLite index, owner-only credentials/jobs, project assets/revisions/artifacts/exports |

Use snake_case JSON keys consistently across API, schema and adapters. `ProjectDocument`, `AssetRecord`, `GenerationRequest`, `GenerationReceipt`, `JobRecord`, `ProposalBatch`, `CompiledProject` and `ExportReceipt` are runtime-validated JSON objects. Python exposes their typed aliases in `contracts.py`; TypeScript types are generated from shared schemas. Request wrappers may use Pydantic, but do not create a second independently evolving project schema. API `GET /api/projects/{id}` returns a `ProjectView` envelope `{document, head_revision_id, last_successful_export, available_generation_results}`; the document itself has no operational job/export fields.

`ProjectDocument` contains project/revision/parent IDs, title, canvas, rational fps, clock/frame count, assets, tracks, clips, captions, motion and source maps. Use UUID hex IDs for projects/assets/clips/tracks; revision IDs are SHA-256 of sorted-key canonical JSON excluding `revision_id`. Include the parent ID. Source times and timeline times are separate fields. Solid-color scenes are an explicit clip variant; media clips require an asset and source interval. A new zero-frame draft with no clips/captions/motion is valid but cannot preview/export. Caption display overrides never overwrite verified source words.

Create test fixtures alongside the owning task: Task 1's `valid_project` and clock fixtures in `apps/api/tests/conftest.py`; Task 2's stores/head fixture there; Task 3's enqueue arguments/API client; Task 4's owned six-second narration and two/one-second footage receipt. Studio tests use `src/test/setup.ts` with an HTTP mock and real shared document fixtures. Structural schema fixtures run in Python and AJV; additional relational timeline checks remain server-authoritative rather than duplicating a second project validator in the studio.

The service interfaces below are the names later tasks consume. Return immutable/copy-on-write documents; never mutate a saved revision in place. Store and API methods return structured errors through one `PixelMotionError` class.

## Task 1: Reproducible engines and validated project contract

**Files:** Create repository/runtime files, `packages/project-schema/*`, `apps/api/pyproject.toml`, `apps/api/src/pixelmotion/{contracts,errors}.py`, `apps/api/tests/{test_contracts,test_vendor}.py`; curate `engines/*`.

**Interfaces:** Produces `validate_document(value: dict) -> ProjectDocument`, `validate_generation_request(value: dict) -> GenerationRequest`, `canonical_revision_id(document: ProjectDocument) -> str`, `frame_ticks(fps: dict) -> int`; Node `vendorSources({sources, destination}) -> manifest` and `inspectTools() -> {ready, tools, errors}`. Errors carry `code`, `item_ids`, `retryable`.

- [ ] **Step 1: Initialize the separate repository and minimal test/dependency manifests.** Copy reviewed documentation; create the branch and ignore private data/virtual environments. Define root npm workspaces for schema, Herk adapter, render runtime and studio; define API uv environment and local editable MoneyPrinter bridge dependency. Install exact resolved dependencies during execution and retain lockfiles. Do not build either application.
- [ ] **Step 2: Write contract/vendor tests.** Assert `240000/30 == 8000`, `240000/60 == 4000`, accepted canvases/rates/limits, rejection of duplicate IDs, invalid/gapped video intervals, missing asset references, unsupported rate, negative/noninteger/unsafe ticks and unknown project keys. Assert equivalent valid/invalid fixtures in Python and the generated studio validator. Vendor tests reject excluded files and source-hash changes.

```python
def test_supported_frame_clock(valid_project):
    assert validate_document(valid_project)["ticks_per_second"] == 240000
    assert frame_ticks({"numerator": 30, "denominator": 1}) == 8000
    assert frame_ticks({"numerator": 60, "denominator": 1}) == 4000
```
- [ ] **Step 3: Run the new tests and verify failure because the validators/vendor functions do not exist.** Command: `uv run --project apps/api pytest apps/api/tests/test_contracts.py apps/api/tests/test_vendor.py -q`.
- [ ] **Step 4: Implement schema, clock validation and curated vendoring.** Preserve exact upstream bytes plus original/patched hashes. Herk allowlist: four license/notice files; canonical `.claude` cut-silences, cut-mistakes and short-form validator scripts; `scripts/preflight.mjs`, `scripts/validate-beat-sync.mjs`; synthetic editing/short-form JSON fixtures; three layout-reference HTML files listed in Task 6. No `.agents` duplication or upstream package install is needed. MoneyPrinter allowlist: license, CLI, config example, pyproject/uv lock, package description; `app` config/models/utils; service import closure including `services/utils/video_effects.py` and `services/data/azure_voices.json`; relevant CLI/task/config/revision test source. Exclude `resource`, WebUI, HTTP/launcher entrypoints and unused UI-only services. Validate the closure using its isolated environment; record any required additional source file before including it.
- [ ] **Step 5: Implement setup/doctor and pass targeted checks.** API Python is managed 3.11. Install MoneyPrinter locked dependencies with `uv sync --project engines/moneyprinter --python 3.11 --frozen --no-install-project` so packaging cannot force-include excluded fonts/music. Execute its source CLI from that environment. Install HyperFrames through the render workspace, without the original Herk package/GSAP. Setup may use compatible existing tools or a pinned, hash-verified per-user FFmpeg/FFprobe bundle with recorded source/license; do not require sudo or mutate system packages. Doctor checks executable/version/codec availability without rendering, downloading models or opening a browser; unavailable tools produce a setup error. Pass Step 3, generate TypeScript types, and verify no schema fixture drift.
- [ ] **Step 6: Commit the validated contract, curated source and runtime metadata.** Message: `feat: establish PixelMotion project contract and reusable engines`.

## Task 2: Owned media and atomic project revisions

**Files:** Create `apps/api/src/pixelmotion/{db,assets,projects,captions}.py`, `apps/api/tests/{test_assets,test_projects,test_captions}.py`, `apps/api/tests/fixtures/`; add caption/asset definitions to the shared schema.

**Interfaces:** Consumes Task 1 contracts. Produces `AssetStore(root, db).admit(project_id: str, stream: BinaryIO, filename: str) -> AssetRecord`, `.resolve(project_id, asset_id) -> Path`, `.verify(project_id, asset_id) -> AssetRecord`; `ProjectStore(root, db).create(title, canvas, fps) -> ProjectDocument`, `.read(project_id, revision_id=None) -> ProjectDocument`, `.save(project_id, base_revision_id, document) -> ProjectDocument`, `.undo(project_id, base_revision_id) -> ProjectDocument`, `.redo(...) -> ProjectDocument`; `parse_srt(data: bytes) -> list[dict]`.

- [ ] **Step 1: Write persistence/admission tests.** Same filename in two projects must remain isolated; symlink/traversal/forged media and altered hashes fail. Failed SQLite commit after writing a revision must not advance the head. A stale save conflicts. Undo/redo restores all source/caption/motion/audio state; a new edit clears redo. Test BOM/CRLF SRT, genuine overlapping cues, zero/negative/reversed bounds and cue overflow past project duration.

```python
def test_stale_save_preserves_head(project_store, saved_project):
    pid, head = saved_project["project_id"], saved_project["revision_id"]
    with pytest.raises(PixelMotionError) as error:
        project_store.save(pid, "0" * 64, saved_project)
    assert error.value.code == "stale_revision"
    assert project_store.read(pid)["revision_id"] == head
```
- [ ] **Step 2: Run `uv run --project apps/api pytest apps/api/tests/test_assets.py apps/api/tests/test_projects.py apps/api/tests/test_captions.py -q` and verify missing-service failures.**
- [ ] **Step 3: Implement immutable assets and revision transactions.** Reuse attributed MoneyPrinter `video_project.py` atomic-write, hash, lock and integrity routines/patterns; do not adopt its narrower scene schema. Stream uploads with a 2 GiB per-asset admission cap, check byte signatures and probe detected media, and store content-addressed bytes beneath the owning project. Never accept a client filesystem path. Revision files publish before a compare-and-swap SQLite head update; unreferenced crash leftovers do not become current. Store timing originals separately from caption display overrides.
- [ ] **Step 4: Implement SRT parsing and history semantics.** Parse UTF-8 with optional BOM, normalize CRLF, require valid numbered/time ranges and preserve display text as plain text. Preserve cue-level granularity and overlaps; validate project bounds at document admission. Hash canonical document content exactly as Task 1 specifies. Preserve last successful export references through new edits and failed operations.
- [ ] **Step 5: Pass Step 2 and contract tests, then commit.** Message: `feat: persist owned media and recoverable project revisions`.

## Task 3: Local control API and supervised durable jobs

**Files:** Create `apps/api/src/pixelmotion/{main,api,security,credentials,jobs,processes}.py`, `apps/api/tests/{test_api,test_jobs,test_processes,test_security}.py`; create `scripts/dev.mjs` process coordination.

**Interfaces:** Consumes asset/project stores. Produces `JobStore.enqueue(project_id, kind, base_revision_id, request, idempotency_key) -> JobRecord`, `.get(job_id)`, `.cancel(job_id)`, `.recover()`; `ProcessSupervisor.run(argv: list[str], cwd: Path, env: dict, job_id: str, deadline_seconds: int) -> ProcessResult`; executor protocol `execute(job: JobRecord, context: JobContext) -> dict`. `JobContext` provides stage/heartbeat/cancel-check and private job directory, without public secret values.

API surface: `GET /api/session`, `GET/POST /api/projects`, `GET /api/projects/{id}`, `PUT /api/projects/{id}/revision`, `POST /api/projects/{id}/edits`, `/undo`, `/redo`, `/assets`, `/generation`, `/proposals`, `/proposals/apply`, `/previews`, `/exports`; `POST /api/projects/{id}/generation-results/{receipt_id}/apply`; `GET /api/projects/{id}/assets/{asset_id}` and `/artifacts/{artifact_id}`; `GET /api/jobs/{id}`, `POST /api/jobs/{id}/cancel`; `GET/POST /api/credentials` returns safe metadata/reference only. All mutations except credential admission reference owned assets, not host paths. Request/result shapes are the shared contracts; revision writes include `base_revision_id`.

- [ ] **Step 1: Write API/job/process tests.** Two enqueue attempts with identical key/digest return one job; changed input conflicts. One media slot survives concurrent admission. Reject wrong Host/Origin, absent mutation session, wrong content type and cross-project asset IDs. Use real harmless child processes to assert cancellation terminates descendants, late completion cannot promote, expired lease cannot spawn a duplicate live owner, and startup preserves queued work while marking orphaned execution interrupted.

```python
def test_idempotent_admission(job_store, enqueue_args):
    first = job_store.enqueue(**enqueue_args)
    again = job_store.enqueue(**enqueue_args)
    assert again["job_id"] == first["job_id"]
    assert again["state"] == "queued"
```
- [ ] **Step 2: Run `uv run --project apps/api pytest apps/api/tests/test_api.py apps/api/tests/test_jobs.py apps/api/tests/test_processes.py apps/api/tests/test_security.py -q` and verify failures.**
- [ ] **Step 3: Implement loopback API/session/credential boundaries.** Dev defaults: API `127.0.0.1:8765`, studio `127.0.0.1:5173`, exact configurable origin allowlist and Vite `/api` proxy. Session cookie is HttpOnly/SameSite=Strict; private credentials use owner-only files and opaque references. Capture engine stderr privately in bounded memory, remove resolved credential values before any diagnostic persistence and expose only safe stage/error fields. Reject arbitrary provider/runtime configuration injection. Routes register executor kinds; unfinished kinds return explicit unsupported errors until their tasks integrate them.
- [ ] **Step 4: Implement transactional job state and process supervision.** Persist PID plus process start identity/group and lease owner to avoid PID-reuse mistakes. Use argument arrays and a new owned process group. Heartbeat/deadline/cancellation values come from Global Constraints. On cancellation update state before termination and recheck it at promotion. Reconcile liveness and validated receipts before retry; never automatically repeat uncertain remote requests. Scheduler and dev launcher terminate owned children on shutdown.
- [ ] **Step 5: Pass Step 2 plus persistence tests and commit.** Message: `feat: supervise local media jobs behind the control API`.

## Task 4: Connected and offline generation to editable timelines

**Files:** Create `adapters/moneyprinter/src/pixelmotion_moneyprinter/{command,config,result}.py`, `patches/moneyprinter/0001-materials-receipt.patch`, `apps/api/src/pixelmotion/{generation,planner}.py`, `apps/api/tests/{test_generation,test_planner}.py`; update schemas, engine manifest and API executor registration.

**Interfaces:** Consumes stores, job context and supervisor. Produces `build_engine_command(request, private_paths, credential_values) -> EngineCommand(argv,cwd,env)`, `parse_engine_result(stdout: bytes, returncode: int) -> dict`, `collect_generation(job: JobRecord, context: JobContext) -> GenerationReceipt`, `prepare_offline(job, context) -> GenerationReceipt`, `plan_timeline(receipt: GenerationReceipt, base: ProjectDocument) -> ProjectDocument`, `apply_generation(project_id, receipt_id, base_revision_id) -> ProjectDocument`.

- [ ] **Step 1: Write generation/initial-planning tests.** Assert supplied script+terms makes no LLM call; missing terms without selected LLM fails admission. Custom narration named `take-02.wav` must survive unchanged and be timed from ffprobe, not upstream's rounded seconds. Supplied SRT/disabled captions must not invoke Whisper. Reject malformed/trailing stdout, missing/extra batch tasks, exit-zero failed/missing artifacts, escaping paths, ambiguous provenance and corrupted media. Offline tests deny all network. Assert five-second ordered placement/repetition, explicit repeated clip IDs, final-frame silence padding, limits and stale-result handling.

```python
def test_short_footage_repeats_deterministically(receipt_six_seconds, empty_project_30):
    doc = plan_timeline(receipt_six_seconds, empty_project_30)
    a, b = receipt_six_seconds["materials"]
    assert [clip["asset_id"] for clip in doc["clips"]] == [a, b, a, b]
    assert doc["frame_count"] == 180
```
- [ ] **Step 2: Run `uv run --project apps/api pytest apps/api/tests/test_generation.py apps/api/tests/test_planner.py -q` and verify failures.**
- [ ] **Step 3: Enrich the narrow materials return and preserve upstream test intent.** Patch only the `stop_at="materials"` state/return block to include already computed `script`, `terms`, `materials`, `audio_file`, `audio_duration` and `subtitle_path`. Update the vendored `test_start_returns_each_intermediate_result` expectation in the explicit patch. No final composition or publishing call is introduced. Manifest records original and patched hashes.
- [ ] **Step 4: Implement isolated single-entry batch CLI execution.** Pass `--batch-file <private-json> --stop-at materials` via the dedicated interpreter, cwd engine root and fresh `MPT_HOME`. Manifest fixes sequential/source matching, five-second shots, rate 1, one video, no background music and explicit requested caption mode. Config sets task-owned materials, Redis/publishing/request logging/reranking off; secrets enter only owner-only config. Require explicit `video_terms` for supplied scripts when no LLM is selected. Edge captions are only valid with synthesized Edge narration; supplied narration uses supplied SRT or disabled captions. Parse exactly one successful batch task and retain its engine UUID internally.
- [ ] **Step 5: Implement validated receipt import and deterministic planning.** Read allowlisted source records from `script.json`, never expose raw params. Resolve paths under the owned job root; copy custom narration there before invoking the engine. Probe actual audio duration; preserve candidate order/provenance and original subtitle files. Snapshot all assets before receipt publication. Offline creation shares validation/planning but bypasses the engine entirely. A completed result for an older head remains pending explicit application. Register generation executor and apply-result route.
- [ ] **Step 6: Pass Step 2 and the patched upstream intermediate-result test in the engine environment; commit.** From `engines/moneyprinter`, run `.venv/bin/python -m pytest test/services/test_task.py -k test_start_returns_each_intermediate_result -q`. Use the already-synced environment without building/installing the vendored package. Message: `feat: import generated media into deterministic editable projects`. Tests use mocked providers; do not claim live generation success.

## Task 5: Atomic editing and reviewed speech cleanup

**Files:** Create `apps/api/src/pixelmotion/{editing,source_maps,proposals}.py`, `adapters/herk/src/{propose,validate}.mjs`, `adapters/herk/tests/propose.test.mjs`, `apps/api/tests/{test_editing,test_source_maps,test_proposals}.py`; update API edit/proposal handlers.

**Interfaces:** Produces `apply_edit(document: ProjectDocument, command: dict) -> ProjectDocument`, `compose_keeps(existing_maps: list[dict], keeps: list[dict]) -> list[dict]`, `propose_cuts(document, speech_group_id, kind) -> ProposalBatch`, `apply_proposals(document, batch: ProposalBatch, selected_ids: list[str]) -> ProjectDocument`; Node `proposeCuts(requestFile, outputDir) -> proposalReceipt`. Commands are `trim`, `split`, `reorder`, `caption`, `audio`, `fit_crop`, `motion_upsert`, `motion_remove`. `/edits` accepts `{base_revision_id, commands:[...]}`: apply each command to a working copy, validate the whole result, then save one atomic revision. Never accept generated HTML.

- [ ] **Step 1: Write editing/map/proposal tests.** Split/reorder retains original asset ranges; B-roll reorder leaves narration/captions unchanged. Linked speech deletion ripples its audio, captions and anchored motion atomically. Test sequential silence→mistake→manual cuts with repeated words, exact one-frame retained segments at 30/60 fps, subframe silence no-op, no removal across retained speech, empty cuts identity and stale revision/mapping rejection. Corrected caption text/grouping passes while true source/timing drift fails; sentence cues cannot enable word-only actions.

```python
def test_one_frame_keep_retains_original_source():
    maps = [{"asset_id": "a" * 32, "clip_id": "b" * 32,
             "source_start": 16000, "source_end": 24000, "start": 0, "end": 8000}]
    assert compose_keeps(maps, [{"start": 0, "end": 8000}]) == maps
```
- [ ] **Step 2: Run `uv run --project apps/api pytest apps/api/tests/test_editing.py apps/api/tests/test_source_maps.py apps/api/tests/test_proposals.py -q` and `npm --workspace adapters/herk test`; verify failures.**
- [ ] **Step 3: Implement canonical tick/frame edits and mapping composition.** Recompute each retained original interval by intersecting existing piecewise maps; retain distinct repeated clip occurrences. Snap effective silence deletions inside actual silence and outside word intervals, showing those effective intervals before application. Do not round-trip canonical state through upstream rounded transcript times or its 0.04-second keep filtering. Reject rate changes, overlap/gap creation, unsupported speech reordering and invalid final duration before save.
- [ ] **Step 4: Wrap canonical Herk helper paths without rendering intermediate videos.** Use `speech.transcript.json --out-dir <out>` for silence/mistake proposals; approved retiming adds `--cuts approved.json`. Never add `--video` or `--apply` in this editing path. Validate the generated `.silence-edl.json`, `.cut-candidates.json`, `.mistakes-edl.json` and transcript files. Mistake detection uses the current saved speech state, not a merely proposed silence result. Public proposals include revision/mapping digest, effective ranges, reason/context and IDs; no raw host paths. Preserve verified transcript projection separately from caption overrides.
- [ ] **Step 5: Pass Step 2, fixture conformance and revision tests; commit.** Message: `feat: preserve original source maps through reviewed editing`.

## Task 6: Native motion and one deterministic composition compiler

**Files:** Create `packages/render-runtime/src/{compile,motion,validate,cli}.mjs`, `packages/render-runtime/templates/{title,lower-third,callout}.mjs`, `packages/render-runtime/tests/{compile,motion,validation}.test.mjs`; create `apps/api/src/pixelmotion/{compilation,media_plan}.py` and tests `test_media_plan.py`; add template lineage to manifest.

**Interfaces:** Produces Node `compileProject(document, assetMap, outputDir) -> CompiledProject`, `validateCompiled(compiled) -> ValidationResult`, `motionFrames(instance, canvas) -> {keyframes,timing}`; Python `prepare_media_plan(document, assets) -> list[MediaStage]`. `CompiledProject` contains revision/compiler/template IDs, fps/frame count, local root HTML and explicit media/audio dependencies; public JSON omits filesystem paths.

- [ ] **Step 1: Write compiler/preset/validation tests.** Compile all three presets at 30/60 fps and all canvases, min/max duration, delayed start, reordered scene placement and hostile plain text. Check finite paused native animations, absolute project delays, pre-entry/post-exit invisibility, exact slot bounds and one root duration. Reject external imports, timers, missing duration and unsafe URLs. Repeated footage must pass asset/hash/bounds checks without changing original source identity. True corruption, missing clips and timeline gaps fail.

```javascript
test('native timing uses the project clock', () => {
  const {keyframes, timing} = motionFrames({template_id: 'title', start: 480000,
    end: 720000, slots: {headline: 'PixelMotion'}}, {width: 1080, height: 1920});
  assert.equal(timing.delay, 2000);
  assert.equal(timing.duration, 1000);
  assert.equal(timing.fill, 'both');
  assert.equal(keyframes.at(-1).opacity, 0);
});
```
- [ ] **Step 2: Run `npm --workspace packages/render-runtime test` and `uv run --project apps/api pytest apps/api/tests/test_media_plan.py -q`; verify failures.**
- [ ] **Step 3: Implement native derivatives with documented lineage.** Reuse eligible markup/layout structure from `style-library/02-kallaway/cards/tier1/t1-section-boxed.html`, `tier2/t2-lt-minimal.html` and `tier2/t2-lb-callout.html`. Replace original copy, AIS tokens/palette, remote fonts and GSAP scripts. Ship original local neutral tokens and a cleared local font with its license. Slots are title `{headline,kicker?}`, lower third `{name,role?}` and callout `{term,detail?}`; templates declare supported canvases and 0.5–10-second bounds. Native WAAPI is synchronous, finite, paused, `fill: both`, with absolute delay. Every composition host without a registry has `data-no-timeline`; no dummy GSAP registration.
- [ ] **Step 4: Implement one compilation/media plan and explicit validator adaptations.** Build frame-rate-normalized source-range clips, caption display layers, crops/fit, motion and separate mixed audio from the saved document. Simultaneous cue captions stack deterministically in saved cue order. Reuse suitable upstream prepared-media/cache helpers instead of legacy final-video assembly. Herk preflight's GSAP-only rule, editorial no-repeat footage rule, exact-caption-copy rule and house-style anchor/cadence rules must not gate native/intentional-repeat/general projects unchanged. Keep originals for provenance; adapter-owned checks preserve hashes, frame/source coverage, correct timing and actual declared anchors, with documented policy changes. Never fabricate source IDs, anchors or `holdReason` values to satisfy a house-style rule.
- [ ] **Step 5: Pass Step 2 plus source-map fixtures and commit.** Message: `feat: compile editable projects to deterministic native motion`.

## Task 7: Preview/export jobs and verified media promotion

**Files:** Create `apps/api/src/pixelmotion/{rendering,exports,previews}.py`, `apps/api/tests/{test_rendering,test_export_races,test_render_media}.py`, `packages/render-runtime/tests/runtime-state.test.mjs`; integrate executor/asset/export routes.

**Interfaces:** Consumes compiled/media plans and job/store interfaces. Produces `ExportService(projects, jobs, assets, supervisor)` with `.render_revision(job: JobRecord, context: JobContext, purpose: str) -> ExportReceipt`, `.promote_export(project_id, revision_id, job_id, receipt) -> bool`, `.start_preview(project_id, revision_id) -> dict`; pure `verify_export(path: Path, document: ProjectDocument) -> dict`. Preview purpose never updates final-export promotion.

- [ ] **Step 1: Write renderer/race/functional-state tests.** Use a fake executable for progress, timeout, malformed output, cancellation-after-encode and old-revision completion races. Prior exports survive failure. Use automated numeric animation-state checks for `t1→t2→t1`, frame zero, delayed entry and final frame without screenshots or visual assertions. Metadata fixtures distinguish damaged caches from damaged originals and reject fps/frame/dimension/A/V mismatch.

```python
def test_cancelled_job_cannot_promote(export_service, cancelled_export_case):
    assert not export_service.promote_export(**cancelled_export_case)
```

The Task 7 fixture cancels the job after a valid encoded artifact exists and asserts the prior export reference remains unchanged.
- [ ] **Step 2: Run `uv run --project apps/api pytest apps/api/tests/test_rendering.py apps/api/tests/test_export_races.py -q` and `npm --workspace packages/render-runtime test`; verify failures.**
- [ ] **Step 3: Implement preparation, HyperFrames invocation and validation.** Run only pinned local executables with argument arrays and bounded process groups. Enforce half-open trim/fit plans, VFR timestamps, stereo 48 kHz mixing, explicit looping/final-frame silence and bounded deterministic limiter. Run adapted document/asset/composition checks and applicable HyperFrames lint before render. MP4 is H.264/browser-compatible pixel format and AAC when audio exists. Record actual tool versions and content hashes in fingerprints; validate cached bytes before reuse. Missing FFmpeg/Chrome/codecs is a clear preflight failure, never a fake success.
- [ ] **Step 4: Implement preview and atomic final promotion.** Use saved-revision compilation for both. Prefer a supervised local HyperFrames preview without assuming embeddability; always supply a studio-playable draft MP4 fallback from the same revision. Only start the upstream viewer if its verified configuration suppresses browser auto-open; otherwise keep the draft-MP4 route and document the optional viewer command. Promotion rechecks job cancellation and head revision in one transaction; obsolete results remain historical. Asset/artifact routes support authenticated byte ranges for scrubbing and never expose engine paths.
- [ ] **Step 5: Run scoped real automated media acceptance once tools are available.** `uv run --project apps/api pytest apps/api/tests/test_render_media.py -q` renders six short synthetic cases (three canvases × two fps), each exercising caption overrides and all three native presets. Probe exact frame count/rate/dimensions and A/V agreement within one frame; assert receipt and source-map correspondence. Use fixtures/local assets only; no provider calls, screenshots, visual comparisons or manual listening. If tools remain unavailable, record these tests as blocked and do not mark export acceptance complete.
- [ ] **Step 6: Pass Step 2 and Step 5, then commit.** Message: `feat: render and promote validated project revisions`.

## Task 8: Studio creation, project library and generation jobs

**Files:** Create `apps/studio/src/{main,App}.tsx`, `src/lib/{api,contracts}.ts`, `src/components/ui/*`, `src/features/projects/{ProjectLibrary,CreateProject,GenerationForm,JobStatus}.tsx`, their `*.test.tsx`, styles and `scripts/check-ui.mjs`.

**Interfaces:** Consumes API endpoints and generated types. Produces typed `api.listProjects/getProject/createProject/uploadAsset/startGeneration/getJob/cancelJob/applyGeneration`; `getProject` returns `ProjectView`. React `ProjectLibrary({onOpen})`, `CreateProject({onCreated})`, `JobStatus({jobId,onResult})`. API client preserves structured error codes, uses session cookies and never logs credential payloads. Preview/export URLs stay project-scoped.

- [ ] **Step 1: Write component/API tests.** Empty library has no invented data; offline form discloses no remote service and never calls generation providers; supplied narration cannot select Edge-derived captions. Supplied script without LLM requires search keywords. Show selected remote services, missing credentials/tools, cancellation and interrupted/retry states. Stale generation results require explicit apply. Credential responses contain references only. Test keyboard entry/focus and structured server errors.

```tsx
it('offers creation without invented projects', async () => {
  render(<ProjectLibrary onOpen={vi.fn()} />); // HTTP mock returns []
  expect(await screen.findByRole('button', {name: 'Create project'})).toBeEnabled();
  expect(screen.queryByText('Demo project')).not.toBeInTheDocument();
});
```
- [ ] **Step 2: Run `npm --workspace apps/studio run test -- src/features/projects` and verify missing-component failures.**
- [ ] **Step 3: Implement project/creation and job surfaces.** Use React/TypeScript and shared Shadcn components; original PixelMotion typographic identity and neutral studio chrome. Raw buttons/form/table primitives live only in `components/ui`. Upload supplied files before admission; use explicit connected/offline mode, canvas and fps. Poll active job state with cancellation/retry controls, clean up polling on unmount and preserve form state on errors. Do not offer unsupported providers or publishing.
- [ ] **Step 4: Implement scoped UI boundary/type checks and pass tests.** `check:ui` parses all TSX and rejects raw/legacy UI primitives outside the canonical layer, including action links without shared adapters. Run `npm --workspace apps/studio run check:ui`, `npm --workspace apps/studio run typecheck`, shared-schema fixture conformance and Step 2. Do not run a Vite build or browser inspection.
- [ ] **Step 5: Commit.** Message: `feat: create editable projects through the PixelMotion studio`.

## Task 9: Studio timeline, captions/audio/motion inspector and revision flow

**Files:** Create `apps/studio/src/features/editor/{Editor,Timeline,Preview,Inspector,CaptionEditor,MotionInspector,ProposalReview}.tsx`, `useProject.ts`, `*.test.tsx`; extend `src/lib/api.ts` for edit/save/undo/redo/proposal/preview/export endpoints.

**Interfaces:** Consumes `ProjectDocument`, `ProposalBatch` and Task 5 commands. Produces `Editor({projectId})`, `useProject(projectId) -> {document,dirty,save,edit,undo,redo,conflict,preview,exportJob}`; all edit requests include base revision. `Preview({revisionId, artifact: {revision_id,url}|null, loading?})` must expose playback/scrubbing even when the external HyperFrames viewer is separate.

- [ ] **Step 1: Write editor behavior tests.** Trim/split/reorder have keyboard-operable numeric/list alternatives; B-roll reorder preserves narration positions; caption correction/motion slots/audio gains round-trip through API and undo/redo. Invalid/dirty/conflicted state blocks export. Mark previews stale after edits; retain unsaved state on save conflict. Show effective cleanup ranges and reasons, require selected review, and reject stale batches. Provide alignment-disabled controls and historical-export labels.

```tsx
it('labels the previous preview after an edit', () => {
  render(<Preview revisionId={'2'.repeat(64)} artifact={{revision_id: '1'.repeat(64),
    url: '/api/projects/p/previews/old.mp4'}} />);
  expect(screen.getByRole('status')).toHaveTextContent('Preview is out of date');
});
```
- [ ] **Step 2: Run `npm --workspace apps/studio run test -- src/features/editor` and verify failures.**
- [ ] **Step 3: Implement editor controls against canonical commands.** Video timeline is sequential with distinct caption/audio/motion tracks. Inspector uses shared controls for fit/crop, gains 0–2, caption display/timing, template slots and 0.5–10-second motion bounds. Map cursor frames to canonical ticks, not a second clock. `edit` stages a local command list; Save sends that batch to `/edits` and replaces the document only on success. Unsaved form intentions remain visible on conflict; do not duplicate server source-map logic in TypeScript. Undo clears/restores pending local command state before calling server history when clean. Reduced-motion preference affects chrome, not authored preview content.
- [ ] **Step 4: Integrate save/history/proposals/playback/export.** Render draft media through a semantic video player with byte-range scrubbing and accessible controls; reuse the supervised upstream preview where practical. Export references a saved revision; show bounded actual job progress and retain previous successful downloads during a failed/new export. No raw engine diagnostics or arbitrary HTML authoring reaches the UI.
- [ ] **Step 5: Pass Step 2, studio project tests, `check:ui` and TypeScript checks; commit.** Message: `feat: edit captions footage audio and motion in one studio`.

## Task 10: End-to-end offline acceptance and runnable repository handoff

**Files:** Create `apps/api/tests/test_offline_workflow.py`, `apps/studio/src/integration/editor-flow.test.tsx`, `scripts/check.mjs`, `.github/workflows/check.yml`, `docs/{SETUP,ARCHITECTURE,THIRD_PARTY,VERIFICATION}.md`; finalize README/setup/dev lifecycle.

**Interfaces:** Consumes all preceding public contracts. Produces `npm run setup`, `npm run doctor`, `npm run dev`, `npm run check`; setup provisions managed environments/locked dependencies and documented local tools, dev serves only loopback, and check runs the scoped functional suite without builds or visual/manual checks.

- [ ] **Step 1: Write integrated tests before wiring the final flow.** Deny network, admit synthetic footage/custom narration/BOM-CRLF SRT, create/import a project, change a clip/caption/title/gain, apply reviewed speech cleanup where aligned, save/reopen/undo/redo, preview/export and validate artifacts. Delete temporary engine data before reopening. Include duplicate filenames in a second project, final-frame padding, stale save/result/cancel races and restart with queued work. Studio integration uses the API contract through an HTTP mock, without opening a browser.

```python
def test_offline_edit_reopen_and_export(api_client, offline_media):
    result = run_offline_case(api_client, offline_media)
    assert result["reopened_revision_id"] == result["saved_revision_id"]
    assert result["export_revision_id"] == result["saved_revision_id"]
    assert result["network_calls"] == 0
    assert result["probed_frames"] == result["expected_frames"]
```

Define `run_offline_case` in this task's test module as the HTTP workflow helper; `offline_media` is generated locally and network denial is enforced by the test harness, not inferred from a counter alone.
- [ ] **Step 2: Run `uv run --project apps/api pytest apps/api/tests/test_offline_workflow.py -q` and `npm --workspace apps/studio run test -- src/integration`; verify any wiring failures.**
- [ ] **Step 3: Complete the startup/check/documentation contract.** Document FFmpeg/FFprobe/Chrome and libx264 requirements with actual resolved versions, local provider configuration, privacy/offline behavior, known first-release limits and upstream lineage. Setup uses locked dependency installs and managed Python; missing system tools produce a documented actionable error rather than silently requiring sudo or marking setup successful. Dev shuts down all owned services on Ctrl+C. CI runs schema/unit/component checks and a media-capable job; live provider tests are separately opt-in. Do not add build/visual checks.
- [ ] **Step 4: Run `npm run check` once, plus Step 2 and Task 7 media acceptance if not already covered by the aggregate.** Re-run only suites justified by final wiring changes. Record commands, passed/blocked results and tool versions in VERIFICATION.md. Run vendor/provenance and secret-exclusion checks before committing. A blocked required media check leaves the first-release acceptance incomplete.
- [ ] **Step 5: Commit and hand off the runnable local repository.** Message: `test: verify the complete editable video workflow`. Report path, startup command, exact test results and remaining limits. No GitHub repository creation, push, deployment, paid generation or publishing is part of this handoff unless separately requested.

## Plan self-review and execution handoff

Root self-review completed: spec sections 1–3 map to Tasks 1/3/8, 4–5 to Task 4, 6–7 to Tasks 1/5/6/9, 8 to Task 2, 9 to Task 3, 10 to Tasks 6/7, 11 to Tasks 8/9 and all section-12 acceptance to Tasks 7/10. The five Review Focus items have explicit owning tests. Interface review clarified empty drafts, the project-view envelope, edit batches, artifact routes and export-service dependency injection. Documentation checks verified relative links, whitespace, code fences, absence of placeholders, ten task sections and ten representative test cases. These are plan checks, not executed application tests. No task may declare a feature supported if its export or recovery gate remains blocked.

Recommended execution method: **Subagent-driven**, because the adapters, canonical mapping, media jobs and studio have distinct reviewable boundaries but must agree on the same document and promotion rules. Keep task implementation and fresh review sequential at those boundaries; parallelize independent research or clearly separated files only after their interfaces are stable. Native execution is also available if the user prefers fewer review passes.

The plan must be reviewed and an execution method selected before scaffolding, in accordance with the active brainstorming/writing-plans workflow. No implementation code or application dependency installation has occurred while preparing this plan.
