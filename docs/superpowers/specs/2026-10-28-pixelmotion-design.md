# PixelMotion unified creative editor — design specification

Date: 2026-10-28, Asia/Manila. Status: **approved specification; implementation plan prepared for review**. The user approved the architecture with “PROCEED”, then approved this written specification by requesting implementation. No product repository, application code, dependency installation, GitHub publication, or deployment has occurred during specification/planning.

## 1. Product and first-release outcome

**PixelMotion — All-in-one creative video editor.** Combine motion, animation, and video editing through **generate → edit → animate → export**, reusing MoneyPrinterTurbo and Herk Edit Kit.

The first release is a single-user, local-first application with a browser studio and supervised local media workers. The standalone implementation destination is `/home/micxsz/projects/pixelmotion`. PixelCore remains a separate application. Current planning files are held in PixelCore and must travel into the new repository at implementation.

A usable release must create an editable project from generated or uploaded media; let the creator trim, split and reorder footage, correct captions, set audio levels and add motion presets; save/reopen the project; and export the accepted edits together. Opening two unrelated upstream interfaces or importing only a flattened MP4 does not satisfy this outcome. A newly created empty project is a valid draft but cannot preview/export before it has a valid nonempty timeline.

The first release supports projects up to 10 minutes and 100 video clips, with portrait 1080×1920, landscape 1920×1080 and square 1080×1080 canvases. Export rates are 30 or 60 fps, default 30. Original source files and their frame-rate metadata are preserved. These are proposed first-release bounds, not limitations claimed for the upstream projects.

Playback speed is fixed at 1× initially. Video scenes use hard cuts. Arbitrary keyframe authoring, speed ramps, reverse playback, general effect plugins, real-time collaboration, hosted tenancy, automatic publishing, and paid text-to-video/image generation are later scope. Existing upstream code for those provider workflows is preserved where eligible but is not advertised as supported studio functionality.

## 2. Reuse and provenance

The [repository analysis](../../pixelmotion/REPOSITORY-ANALYSIS.md) is the source evidence for this design. Use these exact audited snapshots:

| Engine | Commit | Retained responsibilities |
| --- | --- | --- |
| Herk Edit Kit | `10511e5af86fc47756ea89803b397422e2d89284` | Cut proposals, reviewed cuts, transcript/EDL retiming, eligible layout/template resources, structural validators and HyperFrames conventions |
| MoneyPrinterTurbo | `dd5ee71a0fbbb2c06401a7a4401bc83830a7c4d1` | Script/voice/subtitle/material preparation, provider adapters, provenance and compatible prepared-media revision/render utilities |

Vendor curated source snapshots under `engines/herk` and `engines/moneyprinter`. Preserve paths needed by the invoked helpers. Record URL, commit, included/excluded paths, file hashes, retained notices and local patches in `vendor-manifest.json`. Do not nest upstream Git directories or adopt upstream agent instructions as PixelMotion root instructions. Herk's `.claude/skills` are originals; `.agents/skills` are generated mirrors.

Retain MIT copyright notices, Herk pipeline-use permission, HyperFrames Apache-2.0 notices and applicable third-party notices. Exclude AIS branding/showcase assets and uncleared MoneyPrinter songs/fonts. Ship only locally available runtime assets and fonts with recorded redistribution rights. Provider media carries its own provenance and rights metadata; unknown rights stay unknown.

Keep GSAP outside the default studio motion path. Its separate visual-builder restrictions are not settled by either repository's MIT license. Eligible Herk layout/style code can be reused with a native animation adapter. Original GSAP-dependent resources remain clearly identified upstream material; they are not automatically exposed as studio presets.

## 3. Components and dependency boundaries

| Component | Responsibility |
| --- | --- |
| `apps/studio` | React/TypeScript editing interface with shared Shadcn primitives, project library, timeline, inspector and preview controls |
| `apps/api` | Namespaced Python/FastAPI control service, project revisions, asset admission, jobs and media serving |
| `packages/project-schema` | JSON Schema for the canonical document and shared valid/invalid fixtures; API and studio must agree on it |
| `adapters/moneyprinter` | Isolated CLI invocation, private configuration, validated generation receipts and owned-asset import |
| `adapters/herk` | Cut proposals, mapping normalization, adapted validators and composition compilation |
| `engines/*` | Commit-pinned reusable source and explicit patches |
| Local storage | SQLite project/job index plus project-owned immutable media, revision documents, derived artifacts and exports |

Use Node >=22 for the Herk/HyperFrames runtime and a managed Python 3.11 environment for MoneyPrinter's locked native dependencies. Pin HyperFrames to 0.7.109 initially. Keep control-service and engine environments independent; never import MoneyPrinter's generic `app.*` modules into the control service. Pin additional dependencies in implementation lockfiles rather than using unbounded latest versions.

The control service binds to loopback only. One scheduler owns one active media job at a time; queued work is durable. Engine subprocesses receive only the current job's configuration. Keep credentials in owner-only local configuration outside project data; store credential references rather than values in requests and receipts. The local studio initializes an HttpOnly, SameSite=Strict session cookie; mutations require that session, an allowed exact Origin/Host and JSON or the explicitly supported upload content type. Do not enable wildcard CORS. Media routes resolve asset IDs within their project. Browser input cannot select arbitrary host files or execute arbitrary composition code.

First-release generated compositions are trusted, application-authored output with escaped text and allowlisted local asset references. Importing arbitrary HTML/JavaScript is unsupported. This is a local execution model, not a claim that subprocesses are a hosted security sandbox.

## 4. Two complete creation paths

### Connected generation

The creator provides a script or explicitly configures a script-generation provider, chooses Pexels footage, and chooses Edge TTS or supplied narration. For a supplied script, require search keywords unless an explicitly selected LLM will generate them; do not silently invoke MoneyPrinter's default provider for terms. Captions use available narration timing or an imported SRT; captions can also be disabled. Present the selected remote services before starting. Never infer that a service is offline merely because it needs no API key.

Invoke MoneyPrinter CLI with `stop_at="materials"`, a job-specific `MPT_HOME`, `material_directory="task"`, and publishing disabled. Capture actual script, narration, subtitle and material artifacts before final assembly. Use the supplied narration path when present; never assume the audio filename is `audio.mp3`.

### Offline preparation

The creator supplies local footage, script, narration or linked source audio, and optional SRT. This path makes no LLM, speech, stock, telemetry or model-download requests. Missing captions remain disabled until the user supplies timing. Local word transcripts may be imported explicitly; absence of a local ASR model must not trigger a download.

Both paths finish with project-owned originals and a canonical editable revision. Offline mode bypasses network-capable MoneyPrinter generation; it uses the same receipt validation and timeline planner over supplied assets. A final MP4 can be imported as one source clip, but the interface must not imply recovery of its burned captions or original tracks.

## 5. Generation receipt and initial timeline

A generation request identifies project, base revision, normalized request digest and idempotency key. It references admitted immutable inputs and selected provider/credential IDs. An identical key and digest returns the existing job; a changed digest under that key returns a conflict.

A successful `GenerationReceiptV1` records engine commit/adapter version, job/project/base-revision IDs, script/language/search terms, ordered material asset IDs, actual narration asset/duration/origin, original caption asset and parsed cues, and allowlisted source metadata. Every asset has ID, SHA-256, byte size, detected media type and relevant probed duration/dimensions/frame-rate/audio metadata. Receipts contain no absolute paths, credentials, signed provider URLs or raw configuration snapshots.

Validate files, hashes, probe results and all references before atomically publishing the receipt. Copy/snapshot imported artifacts into project ownership before deleting the engine work directory. A zero process exit status alone is insufficient for success.

Initial timeline planning is deterministic. Narration determines generated-project duration, rounded upward to the output frame boundary with silence padding only for that final partial frame. Place footage in receipt order in shots up to five seconds, shortening to available source duration or remaining project duration. Revisit source candidates in the same order when repetition is needed; store each repeated interval as an explicit clip. Reject sources with no complete usable output frame. Save all order/range decisions before preview or export. No renderer reruns random selection.

For uploaded linked speech, source video/audio define the same initial duration and source mapping. B-roll edits preserve independent narration/captions; speech cleanup operates on linked media. Editing displayed caption text does not regenerate narration. A new narration request produces a separate generation result and deliberate import.

If a job finishes against an older base revision, keep its receipt available as a result. Do not overwrite the creator's newer work; applying that result requires an explicit editor action creating a revision from the current head.

## 6. Canonical project and timing contract

`ProjectDocumentV1` has `schema_version=1`, project/revision/parent IDs, title, canvas, rational fps, `ticks_per_second=240000`, frame count, assets, tracks, clips, captions, motion instances and source mappings. Export fps is represented as `{numerator: 30|60, denominator: 1}`. At these rates one frame is exactly 8,000 or 4,000 ticks; one 48 kHz output audio sample is five ticks.

All document times are safe integer ticks and use half-open intervals `[start,end)`. Reject negative/inverted/nonfinite values, duplicate IDs, missing assets and out-of-bounds source references. Video edit boundaries and motion slot boundaries align to output frames. Word timings retain their imported precision converted once into ticks; do not round words independently to frames. Keep original timing files as immutable evidence.

Each media clip records asset ID, track ID, source interval, output interval, linked-group ID when applicable, and fit/crop data. Playback rate must equal 1 in this schema version. For a retained interval, `output_time = output_start + source_time - source_start`. Maintain piecewise maps all the way to original asset coordinates after sequential edits. Variable-frame-rate inputs use probed timestamps to produce derived frame-rate-normalized media; originals do not become proxies or disappear.

One sequential video track covers the intended project duration. Additional tracks hold linked speech/independent narration, optional music, captions and overlapping motion. Gaps are rejected unless represented by an explicit solid-color scene. Overlapping video clips and transitions are outside this version. Audio may overlap on distinct tracks.

Trim and split preserve stable source identity; splitting creates new clip IDs with an ancestor reference. Reorder operates on selected video scenes and preserves source ranges. Reordering B-roll does not move independent narration/captions. Linked speech removals ripple their video/audio, dependent captions and source-anchored motion together. Independent speech-segment reordering is outside v1; do not detach linked media silently.

Audio gain is linear from 0 through 2, with defaults 1 for narration and 0.15 for optional music. Video source audio defaults muted for B-roll and enabled for linked speech. Music looping is represented explicitly in the compiled audio plan. Final audio is stereo 48 kHz; export must not clip through an unbounded gain combination. The mixer applies a deterministic limiter while preserving the creator's relative gains.

## 7. Captions, reviewed cleanup and motion

Caption cues record start/end ticks, editable display text, granularity (`sentence` or `word`), original timing asset and optional verified word references. Keep original ASR words separate from intentional text/grouping overrides. Corrected text survives save, undo and export without becoming a claim that source speech was transcribed again. Sentence SRT cannot become verified word timing by splitting its text.

Word-dependent cleanup and karaoke controls require matching word alignment. Otherwise show the missing-alignment reason and retain ordinary cue captions. Caption cues must stay inside project duration. Removing linked speech removes/retimes affected cues through the source map; crossing words cannot silently become zero-duration retained words.

Herk silence/mistake helpers produce proposals against a revision and selected linked-speech source. Show intervals, transcript context and reason; no proposal changes the timeline until the user selects and applies it. Apply one selected batch as one revision. Reject stale proposals after their source mapping changes. Silence-cut quantization must retain spoken word intervals; empty approved cuts are an identity edit. Adapt Herk's validator so intentional caption corrections are accepted while timing/source drift still fails.

Ship a small allowlist of three motion presets: title, lower third and callout. Each has a stable template/version ID, supported aspect ratios, required text slots, local assets, colors, position, start frame and duration. V1 duration is 0.5–10 seconds and must fit inside the project. Text is plain text. Do not expose the 406 draft cards as a verified supported catalog.

Reuse eligible Herk composition structure/layout resources and replace their GSAP scripts for these starter effects with paused native Web Animations API animations. HyperFrames 0.7.109's published source maps to commit `12fd6d9087fab1347f8737c34901e3db61e4dfee`; its [pinned WAAPI contract](https://github.com/heygen-com/hyperframes/blob/12fd6d9087fab1347f8737c34901e3db61e4dfee/skills/hyperframes-animation/adapters/waapi.md) and adapter code support deterministic seeking. Initially compile all presets into one root composition. Create finite animations synchronously, set `fill: "both"`, pause immediately and use absolute project-time delays; do not assume automatic clip-local time offsets. Add `data-no-timeline` to every composition host without a registered timeline, declare explicit dimensions/duration, and avoid render-critical timers, callbacks or independent clocks. This is source-level compatibility evidence, not a completed render; automated timing/render acceptance remains required before release.

## 8. Revisions, save, undo and recovery

The canonical JSON document is the editing source of truth; generated HTML, engine EDLs, proxies and renders are derived artifacts. Each committed editing action or applied cleanup batch is an atomic immutable revision. SQLite stores the current head and export references. Derive a revision ID from deterministic, sorted-key JSON of the document excluding its own revision ID; include the parent ID so history remains explicit. Publish the immutable revision file before the database transaction advances the head. A crash before that transaction may leave an unreferenced file; it must not advance the head during recovery.

Save requests include the base revision. A stale base returns a conflict and preserves both the server head and unsaved editor state. Undo/redo persists the complete canonical state, including captions, mappings, audio and motion. Undo creates a new head restoring the chosen prior document state; redo restores the undone state. A new edit after undo clears the redo branch while retaining revision history.

Reuse MoneyPrinter's audited `video_project.py` code/patterns for atomic writes, content-addressed assets, locks, dependency fingerprints, artifact validation and successful-export promotion, retaining notices. Its strict prepared-scene schema is not PixelMotion's schema. Reuse compatible preparation stages behind the adapter; there is one canonical PixelMotion project and export job, with no separate legacy `generate_final_videos` export for edited projects.

Cache fingerprints include canonical revision, input hashes, adapter/template versions and actual toolchain versions. Damaged derived artifacts are rebuilt. Damaged originals fail with the affected asset ID; never treat a cache copy of unknown integrity as an original. Last successful exports remain accessible if a new export fails.

## 9. Jobs, cancellation and errors

SQLite is authoritative for jobs. States are `queued`, `running`, `importing`, `succeeded`, `cancelling`, `cancelled`, `failed`, and `interrupted`. Record stage, timestamps, worker owner/heartbeat, attempt, request digest, completed receipt/export and structured failure details. One local media slot includes generation, normalization and export; engine-internal limits are not an additional scheduler.

Workers heartbeat every five seconds; an expired 30-second lease is not sufficient to start a duplicate process. Reconcile recorded process ownership and completed receipts first. On startup, orphaned running/importing jobs become interrupted; queued jobs remain queued. A valid completion receipt may be recovered without repeating work. Uncertain remote/provider acceptance requires explicit retry and must not be reissued automatically.

Cancellation marks the job before terminating its entire owned process group, allows five seconds for termination, then force-stops remaining children. Promotion rechecks cancellation state transactionally. Cancellation cannot publish success afterward or delete prior project revisions/exports. Retain partial work separately for diagnosis and delete private credential-bearing runtime configuration once owned processes have stopped.

Use a 30-minute deadline for one generation or export attempt and 10 minutes for a preparation/probe stage; deadline failures are explicit and retryable without silently restarting remote operations. Report stage and the last bounded progress observation; do not invent percentages when an engine has none.

Errors use `{error:{code,message,item_ids,retryable}}`. Distinguish validation, missing alignment/tool/credential, unsupported feature, provider failure, import-integrity failure, stale revision/proposal, timeout, cancellation and interrupted execution. No failed operation replaces the current valid revision or last successful export.

## 10. Preview and final export

Compile a saved revision into one scoped HyperFrames composition: frame-normalized source scenes, deterministic native motion, captions, and an explicit audio plan. Use local media and font assets. Generated text is escaped; reject external runtime URLs and unsupported active content. Source crop/fit and aspect-ratio changes are saved decisions, not renderer guesses.

Reuse HyperFrames preview capabilities with a controlled local preview process. The studio provides project controls and marks preview stale after edits. Direct iframe embedding is optional; if the pinned preview cannot be embedded safely, use a studio-controlled media preview derived from the same compiled revision and provide the upstream preview as an optional separate viewer. The first release still requires in-studio playback/scrubbing and editing controls.

Every preview/export identifies revision, compiler/template/toolchain versions, frame count and fps. Validate the document, asset integrity, adapted Herk contracts, applicable anchors and HyperFrames lint before render. Do not apply the beat-anchor validator to compositions for which that contract is inapplicable.

Final export is MP4/H.264 with AAC audio when audio tracks exist. Normalize pixel format for browser compatibility. ffprobe-based automated checks require exact intended video frame count, expected dimensions/rate, and A/V duration agreement within one output frame. A receipt records hash, size, media metadata and revision. Promote the export only when validation succeeds and it still corresponds to the current revision; an older revision's completed export remains a labeled historical result.

Unsupported edits must return `unsupported_export_feature` with affected IDs; silently dropping captions, crop, source trims, audio or motion is forbidden. Support for all three accepted motion presets and caption editing in export is a release gate. This is a structural/media acceptance requirement, not a claim of visually approved output.

## 11. Studio behavior

The application opens to real local projects and a create/import action. Creation chooses connected generation or supplied media, script/audio/caption options, canvas and fps. Provider errors stay attached to that job with recovery actions; the project library never shows invented output or metrics.

The editor contains an asset panel, preview with playback/scrub controls, layered timeline and selected-item inspector. Core controls cover trim/split/reorder, caption text/timing, audio gain/mute, fit/crop and supported motion slots. Provide keyboard-accessible alternatives to timeline dragging, visible focus, labeled controls and reduced-motion handling in the application chrome. Preview content retains its authored animation.

Use shared Shadcn components in the new studio's canonical UI layer. Application features must not introduce raw form/action/table primitives outside that layer. Add a scoped `check:ui` automated boundary check for the studio; this does not mean importing PixelCore's Vue primitives into React. Unsaved/invalid edits cannot trigger export. Job status, stale previews, save conflicts and generation results waiting for import must remain visible without implementation jargon.

Use the PixelMotion name and a simple original typographic identity until a separate brand direction is supplied. AIS marks and example content are excluded. This specification defines behavior and layout responsibilities, not a finished visual brand.

## 12. Acceptance evidence and implementation boundaries

Before declaring the first release usable, targeted automated checks must prove:

1. Offline media/script/narration/SRT → owned assets → editable timeline → changed clip/caption/title → saved/reopened revision → validated MP4, with network access denied.
2. Mocked connected generation validates CLI JSON, actual custom/generated audio, subtitle granularity, provenance and task-owned material import; deleting the engine directory leaves imported assets usable. Live credentials are optional for automated tests and no live success is claimed without a run.
3. Idempotency conflicts, stale generation results, stale saves and stale cleanup proposals do not overwrite newer edits or start duplicate work.
4. Sequential silence/mistake/manual cuts preserve original mapping and linked captions; empty cuts preserve identity. Sentence cues cannot enable word-only features.
5. Reopen and repeated export preserve exact saved clip order/ranges and motion choices; B-roll reorder leaves independent narration timing unchanged.
6. All three motion presets and intentional caption corrections compile and export at 30/60 fps in supported aspect ratios; unsupported fields fail explicitly. Repeated seeking `t1 → t2 → t1`, delayed preset entry, frame zero and the final frame produce identical recorded animation state at the same time. Source timestamps, VFR normalization, final-frame padding and audio gain are checked with synthetic fixtures and media metadata.
7. Undo/redo restores the complete linked state; failed compilation/render cannot replace a prior export. Old-revision renders cannot promote over a newer head.
8. Cancellation/deadline/restart terminate owned media children, preserve valid revisions, and report recoverable state without repeating uncertain provider operations.
9. Traversal, symlink escape, forged media types, missing/corrupt assets, invalid intervals, duplicate IDs, unescaped text and external runtime references fail at the correct boundary. Different projects with identical filenames remain isolated.
10. Vendor snapshots retain notices and exclude uncleared assets. Credentials do not enter documents, receipts, logs or browser responses. Studio component and schema/TypeScript checks pass.

Follow the user's verification policy: automated checks by default; no routine frontend/backend builds; no visual tests, browser-based inspections or manual verification without an explicit request. Automated media rendering and ffprobe assertions exercise product output, not a frontend/backend build. Do not describe them as visual approval.

Current evidence remains source analysis plus Herk's 11 passing existing unit tests. FFmpeg/FFprobe were unavailable on PATH during analysis; a later runtime preflight must explain missing tools and use an explicit documented setup path. No render, connected-provider run or browser inspection has verified the proposed integration yet.

The [implementation plan](../plans/2026-10-28-pixelmotion-implementation.md) organizes this product into independently testable milestones: owned project/revisions and vendor provenance; generation-to-timeline adapters; editing/cleanup and deterministic composition; integrated studio/export acceptance. The plan still requires review before scaffolding.

## 13. Review record

- User request: merge both existing projects into PixelMotion rather than rebuilding their engines from scratch.
- User choice: prioritize one generate-then-refine workflow.
- User approval: proceed with the proposed standalone, local-first studio, pinned engines and shared editable project architecture.
- Decisions proposed by this written specification: exact initial feature bounds, React/FastAPI shell, offline/connected creation contracts, native motion starter presets, canonical clock, job/revision semantics and acceptance gates.
- Written-spec approval: user requested implementation after the written-spec review handoff. Planning clarifications explicitly cover empty drafts and the upstream keyword-generation seam.
- Next required review: the implementation plan and execution method. No product implementation or remote publication has occurred.
