# PixelMotion repository analysis and merge recommendation

Prepared 2026-10-28, Asia/Manila. This is the source-backed analysis behind the architecture the user subsequently approved with “PROCEED”. The [formal specification](../superpowers/specs/2026-10-28-pixelmotion-design.md) is approved; the [implementation plan](../superpowers/plans/2026-10-28-pixelmotion-implementation.md) is prepared for review. No PixelMotion application, standalone repository, GitHub repository, or deployment has been created. PixelCore application code is unchanged.

## Intended product

**PixelMotion — All-in-one creative video editor.** Motion, animation, and video editing in one project workflow.

The user selected **generate a video, then refine it with editing and motion graphics** as the first usable version's priority. Success means that generated footage, narration, captions, and motion remain editable together; saving and reopening a project must preserve those editing decisions.

The approved architecture uses a separate, local-first repository at `/home/micxsz/projects/pixelmotion`, with a browser studio and local media workers. A hosted multi-user service is a later deployment decision. The repository has not yet been created; implementation-plan review is the current handoff.

## Audited sources

| Source | Audited commit | Observed runtime |
| --- | --- | --- |
| [Herk Edit Kit](https://github.com/nateherkai/herk-edit-kit/tree/10511e5af86fc47756ea89803b397422e2d89284) | `10511e5af86fc47756ea89803b397422e2d89284` | Node >=22; HyperFrames 0.7.109; GSAP 3.14.2; FFmpeg/FFprobe; Chrome/Chromium for rendering |
| [MoneyPrinterTurbo](https://github.com/harry0703/MoneyPrinterTurbo/tree/dd5ee71a0fbbb2c06401a7a4401bc83830a7c4d1) | `dd5ee71a0fbbb2c06401a7a4401bc83830a7c4d1` | Python >=3.11; MoviePy 2.2.1; FastAPI; Streamlit; FFmpeg; optional provider/ML dependencies |

Analysis clones are cached at `/home/micxsz/.graphify/repos/nateherkai/herk-edit-kit` and `/home/micxsz/.graphify/repos/harry0703/MoneyPrinterTurbo`. These are research inputs, not the new product repository. Upstream instruction files were inspected as source material, not adopted as PixelMotion's root instructions.

## Similarities and differences

| Area | Herk Edit Kit | MoneyPrinterTurbo | PixelMotion decision |
| --- | --- | --- | --- |
| Primary input | Existing recordings, transcripts, a creative brief | Topic/script and generation settings; local media is also supported | Support a topic or uploaded footage |
| Main strength | Reviewed edits, storytelling, precise motion compositions | Automated script, voice, material, subtitle, and video generation | Preserve both engines' strengths |
| User surface | Agent skills and CLI helpers; HyperFrames Studio preview | Streamlit WebUI, FastAPI, CLI | One project-oriented studio controls both |
| Picture assembly | HTML/CSS compositions with timed media and seekable animation | MoviePy/FFmpeg assembly and effects | Compile one saved timeline into the appropriate renderer |
| Speech/captions | Word-timed JSON and EDL-based retiming | SRT; provider-dependent timing granularity | Preserve both cue and word timing explicitly |
| Editing data | Transcripts, cut decisions, EDLs, plans, HTML | Task parameters/artifacts; optional local scene revisions | Add a versioned interchange project model |
| Motion | Reusable cards, scene templates, GSAP/HyperFrames conventions | Subtitle animation and video effects, with no equivalent general motion-card workflow | Reuse eligible Herk composition resources |
| Render/tool overlap | FFmpeg, media probing, transcription, captions, audio, project files | FFmpeg, media probing, transcription, captions, audio, project files | Share assets and decisions; avoid generating the same media twice |
| Distribution | Toolkit with original code and separately governed assets/dependencies | MIT code with bundled resources requiring separate review | Curate the vendor payload and retain notices |

Neither source alone supplies the complete unified PixelMotion experience. HyperFrames already supplies a useful composition preview and scrubber; MoneyPrinterTurbo already supplies a generation interface. New project controls and conversion code are still required to make them operate on the same editable document.

## Actual code relationships and integration seams

### MoneyPrinterTurbo: reuse generation before final assembly

The verified call chain is `task.start → _run_pipeline → generate_script / generate_terms / generate_audio / generate_subtitle / get_video_materials → generate_final_videos → video.combine_videos`.

Source: [task.py](https://github.com/harry0703/MoneyPrinterTurbo/blob/dd5ee71a0fbbb2c06401a7a4401bc83830a7c4d1/app/services/task.py), [video.py](https://github.com/harry0703/MoneyPrinterTurbo/blob/dd5ee71a0fbbb2c06401a7a4401bc83830a7c4d1/app/services/video.py), and [cli.py](https://github.com/harry0703/MoneyPrinterTurbo/blob/dd5ee71a0fbbb2c06401a7a4401bc83830a7c4d1/cli.py).

`stop_at="materials"` is the best initial handoff. It prepares the script, narration, subtitles, and footage before making a flattened final video. The CLI exposes this stage and emits machine-readable result JSON; the existing public HTTP routes do not expose a materials-stage operation. A subprocess adapter therefore requires less upstream change than adding an HTTP endpoint first.

The materials result only returns material paths. The adapter must separately retain and validate `script.json`, generated or custom narration, `subtitle.srt` when enabled, source durations, and provenance. Do not assume narration is always `audio.mp3`: custom and reused audio can live elsewhere. Set `app.material_directory="task"` where applicable so downloaded materials have a clear task-owned location.

Material lists are not finished timelines. `combine_videos()` makes clip ordering, source range, speed, transition, crop, and repetition decisions during assembly without exporting a complete persistent edit manifest. PixelMotion should create its own deterministic timeline from retained materials, or extend this narrow seam to emit the actual decisions before rendering. A final MP4 cannot recover burned captions, separate audio tracks, discarded pixels, or original cut decisions.

MoneyPrinterTurbo also contains [video_project.py](https://github.com/harry0703/MoneyPrinterTurbo/blob/dd5ee71a0fbbb2c06401a7a4401bc83830a7c4d1/app/services/video_project.py) and [local-project documentation](https://github.com/harry0703/MoneyPrinterTurbo/blob/dd5ee71a0fbbb2c06401a7a4401bc83830a7c4d1/docs/video-projects.md). This is valuable existing work: immutable prepared-media revisions, hashes, stage dependencies, artifact reuse, cancellation, and export promotion. Its schema accepts scenes with footage/audio/narration/duration and render settings; it does not implement word-aligned subtitles, transitions, or motion overlays. Reuse compatible revision and rendering behavior through an adapter; do not relabel this limited scene schema as a full editor timeline.

### Herk: reuse cutting, retiming, motion resources, and composition preview

Source: [editing workflow](https://github.com/nateherkai/herk-edit-kit/blob/10511e5af86fc47756ea89803b397422e2d89284/docs/WORKFLOW.md), [scripts](https://github.com/nateherkai/herk-edit-kit/tree/10511e5af86fc47756ea89803b397422e2d89284/scripts), and [Codex skill mirrors](https://github.com/nateherkai/herk-edit-kit/tree/10511e5af86fc47756ea89803b397422e2d89284/.agents/skills). Upstream maintains originals in `.claude/skills` and generates `.agents/skills`; retain that distinction when carrying changes forward.

The useful workflow is source media + word transcript → silence cuts → reviewed mistake cuts → retimed transcript → story/motion plan → timed HTML composition → HyperFrames render. Existing helpers generate candidate cuts and apply reviewed decisions. PixelMotion should show those decisions for review rather than automatically accepting all candidate mistakes.

Retain the helpers, original source media, reusable eligible templates, style manifests, beat validation, and preflight logic. The package also includes synthetic starter/fixture material that does not require paid API keys. Its advertised 406 cards are drafts, not a verified production component catalog.

`npx hyperframes preview` serves the composition and opens its existing Studio with hot reload. Reuse that preview capability where practical. Herk does not ship its own standalone studio application or project-service API; embedding/proxy compatibility of its pinned HyperFrames preview has not been tested. The new product still needs controls that modify the saved project and compile it into compositions.

## Format mismatches that the merge must solve

1. **Sentence cues and word alignment:** Herk cutting needs `{words: [{text, start, end}], audio_duration_secs}` on the exact input timeline. SRT sentence cues are insufficient for accurate word cuts or karaoke. Preserve caption granularity; obtain real provider word timestamps or perform alignment when that feature needs them. Never synthesize precise word times by evenly splitting a sentence.
2. **Different EDL conventions:** Herk helpers use `source_start/source_end` and `keep_ranges`; the short-form plan validator expects fields including `sourceStart/sourceEnd` and `edit-decisions.keeps`. Its existing `video-use-to-hyperframes-transcript.mjs` is an adapter for a different EDL format, not a MoneyPrinter importer.
3. **Chained edits:** Successive cutting stages describe mappings relative to their current input. Compose those mappings to preserve original source provenance across silence removal, mistake cuts, and later edits.
4. **Timing:** Keep one canonical timebase and rational frame rate; preserve source rates and round only at renderer boundaries. MoneyPrinter's current video processing commonly uses 30 fps; Herk includes 30 fps and 60 fps workflows. Do not silently equate these clocks.
5. **Revision schemas:** The existing MoneyPrinter local project schema rejects unknown fields. A richer PixelMotion project needs explicit adapter conversion; adding motion fields to that upstream JSON will fail validation.
6. **Assets and paths:** Replace engine-local absolute paths with validated project-owned asset references, hashes, and source metadata. Resolve engine-specific paths only inside workers.

## Merge approaches

| Approach | Benefit | Cost / suitability |
| --- | --- | --- |
| **Pinned engines + shared project + unified studio (recommended)** | Preserves working generation/edit/render code; one workflow and editable asset model | Requires adapters, project persistence, worker supervision, and studio controls |
| Launcher around existing Streamlit and HyperFrames Studio | Fastest way to use both tools locally | Two separate experiences; does not satisfy the selected shared-editable-project goal by itself |
| Rewrite both engines in one language/framework | One implementation stack | Discards reusable work and creates the largest maintenance and validation burden |

Recommended source strategy: vendor a curated, commit-pinned snapshot of each engine, preserve original relative paths where required, record upstream URLs/hashes and explicit local patches, and keep engine dependencies independent. Exclude Git metadata, secrets, caches, generated renders, excluded brand assets, and uncleared media. A provenance manifest makes later upstream updates reviewable.

## Recommended product architecture for review

Use a thin PixelMotion control layer above the reusable engines. A namespaced Python/FastAPI API would fit the existing generation ecosystem; a TypeScript studio would manage projects, tracks, text, and preview controls. Framework selection is proposed, not yet fixed by an approved spec.

```text
Topic or uploaded footage
          ↓
MoneyPrinter generation / original-media import
          ↓
Project-owned footage + narration + captions + provenance
          ↓
Versioned PixelMotion project and editable timeline
          ↓
Trim/reorder • captions • audio • motion compositions
          ↓
Herk tools + HyperFrames / compatible FFmpeg renderer
          ↓
Preview, export receipt, and reopenable project
```

The shared project should describe immutable original assets, stable clip/track IDs, source ranges, output positions, playback speed, crop/fit, audio gains, caption granularity, editable motion parameters, and render settings. Derived engine artifacts must be regenerable from a saved revision. Credentials belong outside project manifests.

Run MoneyPrinter in its own Python process/environment and the Herk/HyperFrames toolchain in its own Node environment. No direct Python dependency conflict was established; isolation is useful because MoneyPrinter uses global `app.*` imports, configuration, state, provider adapters, and native ML dependencies. Its `MPT_HOME` setting can isolate runtime directories. A subprocess boundary alone is not a security sandbox.

Proposed repository responsibilities, without scaffolding them yet:

- `apps/studio`: project library, editing controls, inspector, preview, save/reopen, undo/redo.
- `apps/api`: namespaced PixelMotion project and job control.
- `packages/project-schema`: versioned interchange contract and validation fixtures.
- `adapters/moneyprinter` and `adapters/herk`: engine conversion and execution boundaries.
- `engines/moneyprinter` and `engines/herk`: curated upstream snapshots and retained notices.
- `vendor-manifest.json` and `patches`: reproducible provenance and small, explicit upstream changes.
- Ignored project storage: originals, revisions, caches, previews, and exports.

Implementation should first prove the editable generation-to-composition handoff with a synthetic fixture, then deliver studio editing and motion/export on that same contract. The first usable release must complete the selected end-to-end workflow; a launcher alone is not that release. Multi-user collaboration, arbitrary visual keyframe authoring, and publishing need their own later scope decisions.

## License and resource decisions

Both projects publish original code under MIT: retain the [Herk notice](https://github.com/nateherkai/herk-edit-kit/blob/10511e5af86fc47756ea89803b397422e2d89284/LICENSE) and [MoneyPrinter notice](https://github.com/harry0703/MoneyPrinterTurbo/blob/dd5ee71a0fbbb2c06401a7a4401bc83830a7c4d1/LICENSE). Herk's imported pipeline resources also require retaining [their use-permission notice](https://github.com/nateherkai/herk-edit-kit/blob/10511e5af86fc47756ea89803b397422e2d89284/licenses/PIPELINE-USE-PERMISSION.txt). Its [third-party notices](https://github.com/nateherkai/herk-edit-kit/blob/10511e5af86fc47756ea89803b397422e2d89284/THIRD_PARTY_NOTICES.md) identify HyperFrames Apache-2.0 and separately governed dependencies/assets.

Herk's license explicitly excludes AIS brand assets from reuse. Use PixelMotion branding and eligible neutral resources; do not redistribute its showcase videos as PixelMotion-owned examples. MoneyPrinter's own README identifies default music sourced from YouTube; accompanying font/music grants were not established by this audit. Exclude uncleared bundled songs/fonts and use separately licensed replacements or user-provided media.

GSAP has its own [standard license](https://gsap.com/community/standard-license/), which restricts certain competing visual animation builders and explicitly allows AI-generated code. Applicability to PixelMotion's exact visual-authoring scope is unresolved; do not claim the source repositories' MIT grants settle it. Keep animation runtime behind an adapter and resolve suitability before promising unrestricted visual animation authoring. Current HyperFrames documentation describes alternate animation runtimes, but their drop-in compatibility with Herk's pinned version and GSAP cards was not established.

## Execution constraints discovered

- MoneyPrinter's API allows access when its configured API key is empty. Do not use that default as a hosted project-authorization boundary.
- MoneyPrinter supports automatic cross-posting after full video generation. The PixelMotion adapter must disable inherited publishing configuration for the requested generate/edit/export workflow.
- Engine queue limits/state alone do not establish durable job leases, restart recovery, or a global concurrency limit across multiple API workers. PixelMotion needs explicit job ownership and recovery behavior.
- Browser-rendered compositions execute HTML/JavaScript. Hosted rendering would require isolated browser/filesystem/network access; this analysis did not validate a hosted deployment.
- Local automated tool discovery found Node 24.21.0, Python 3.14.4, uv, Git, and Chrome. FFmpeg/FFprobe and GitHub CLI were unavailable on PATH. No media render was attempted and no product dependencies were installed. Choose a managed Python version supported by the locked native dependencies rather than assuming system Python 3.14 works.

## Verification evidence and limits

Herk's existing `node --test tests/*.test.mjs` suite passed **11/11** without installing dependencies, running media renders, or opening a browser. MoneyPrinter was inspected structurally and through source; its application suite was not run and no runtime compatibility claim follows from this audit.

Graphify was used for scoped code relationships in both engines, avoiding bundled media and hundreds of motion-card HTML files. MoneyPrinter's 64-file application graph had 1,679 nodes and 3,904 undirected edges. Its diagnostics reported seven self-loops and 147 same-endpoint relation collapses, with no missing/dangling endpoints. Herk's 28-helper-file graph had 387 nodes, 469 directed edges, and 24 communities, with four self-loops and three collapsed relation variants, and no missing/dangling endpoints. Those graph limitations mean exact call and artifact claims above were verified against source, rather than inferred solely from graph traversal. Neither structural graph captures the complete file/process handoffs between tools, and no cross-engine compatibility is implied by a graph edge.

Cached graph reports: `/home/micxsz/.graphify/analysis/herk-edit-kit-source-10511e5/graphify-out/GRAPH_REPORT.md` and `/home/micxsz/.graphify/repos/harry0703/MoneyPrinterTurbo/graphify-out/GRAPH_REPORT.md`. The combined analysis graph is stored separately from PixelCore's existing graph at `graphify-out/pixelmotion/cross-repo-graph.json` (2,066 nodes; 4,373 edges). A broad combined query returned 381 candidates and was truncated to a 1,000-token output budget; direct source reads and narrower per-engine traces support the findings above.

Jev 0.7.0 authentication status succeeded. A secret-free choice request containing only public upstream architecture and the requested goal selected the adapter/shared-project approach. This is advisory; source inspection supports the recommendation independently.

No frontend/backend builds, browser inspections, visual tests, paid generation, or publishing were performed. PixelCore frontend files were not changed, so its `check:ui` check was not applicable to this documentation-only analysis.

Future targeted automated acceptance checks should prove:

- An offline fixture imports retained generation artifacts, edits a clip/caption/title, exports, and reopens with the same saved decisions.
- Clip ranges, speed, crop, track order, gains, captions, motion parameters, and original source mappings survive save/reopen and sequential edits. Source clip order and chosen transitions remain identical across repeated exports of the same revision; upstream random selection must not rerun during export.
- Sentence cues remain sentence cues; missing word alignment gives a clear validation result.
- Export timing agrees with the saved project within one output frame, including narration shorter/longer than footage and mixed source frame rates.
- Identical filenames across projects cannot overwrite or expose another project's media; path traversal/symlink inputs fail.
- Worker failure, timeout, cancellation, and interrupted writes leave recoverable project state and no promoted partial export.
- Upstream snapshots retain notices and exclude uncleared assets; offline tests make no provider or publishing calls.

Application tests and schema/adapter checks should be scoped to implementation changes. Preserve the repository policy against routine builds and visual/manual verification without an explicit request.

## Review handoff

The user selected the product workflow and approved the recommended standalone, local-first studio with curated pinned engines and a shared editable project format.

The approved [formal design specification](../superpowers/specs/2026-10-28-pixelmotion-design.md) is the product contract. Review the [implementation plan](../superpowers/plans/2026-10-28-pixelmotion-implementation.md) and select its execution method before scaffolding, as required by the active brainstorming/writing-plans workflow. The merger has not been implemented.
