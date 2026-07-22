# cjm-transcript-graph-schema

<!-- generated from the context graph by `cjm-context-graph readme` — do not edit by hand; edit the graph (the urge to hand-edit = move it on-graph) -->

Audio-transcript layer schema for context graphs: Source, AudioSegment, Transcript, and Segment nodes with deterministic identity tuples and graph-node mapping, shared by the transcription, decomposition, and correction workflow cores.

## Modules

- **`cjm_transcript_graph_schema.schema`** — The audio-transcript layer schema (where-graph-begins locked layer schema): Source -> AudioSegment(coarse boundary) -> AudioRendition(model-input: raw | vocals | ...) -> Transcript(per-transcriber variants) emitted by transcription, extended with the fine Segment spine (per-rendition) by decomposition. Deterministic identity tuples per the stage-5 ratified rule; the AudioRendition node lets raw + preprocessed model-inputs of one boundary coexist in one graph. Document from the pre-CR-18 era dissolves into Source.

## API

### `cjm_transcript_graph_schema.schema`

- `AudioRenditionNode` _class_ — A model-input rendition OF an AudioSegment — the materialized 16k-mono WAV
- `AudioSegmentNode` _class_ — Coarse ~5-min spine member: a BOUNDARY range of the Source (an audio fact),
- `CollectionNode` _class_ — An intrinsic collection (book, podcast series, lecture course) — the
- `SegmentNode` _class_ — Fine spine member: one VAD chunk — IMMUTABLE audio range + CORRECTABLE
- `SourceNode` _class_ — The provenance root: one ingested media file.
- `TranscriptGraphLabels` _class_ — Node labels of the audio-transcript layer schema.
- `TranscriptNode` _class_ — One transcriber's text for one AudioRendition (per-transcriber variants at
- `TranscriptSliceRef` _class_ — One per-transcriber char-range reference for a fine Segment: where this
- `audio_rendition_node_id` _function_ — AudioRendition identity = (audio segment, preprocessing chain).
- `audio_segment_node_id` _function_ — AudioSegment identity = (source, boundary range).
- `collection_edges` _function_ — Membership edges for a collection (ae3464fc: ORDER IS OPTIONAL).
- `collection_node_id` _function_ — Collection identity = the NORMALIZED TITLE (ratified fork, hub-session
- `normalize_collection_title` _function_ — Normalize a collection title for identity derivation.
- `segment_node_id` _function_ — Fine Segment identity = audio-side only (audio rendition, VAD config, chunk
- `source_node_id` _function_ — Source identity = the ingested file's content hash (Thread-1 ingested-root identity).
- `transcript_node_id` _function_ — Transcript identity = (audio rendition, transcriber, config) — MIRRORS the

## Dependencies

**Depends on:** `cjm-context-graph-layer`, `cjm-context-graph-primitives`
**Used by:** `cjm-context-graph-layer`, `cjm-transcript-correction-core`, `cjm-transcript-correction-tui`, `cjm-transcript-decomp-core`, `cjm-transcription-core`
