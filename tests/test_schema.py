"""Tests for cjm_transcript_graph_schema.schema — identity tuples + wire shapes.

Projected from the schema notebook's four test cells at the c25780e8 flip."""
from cjm_context_graph_primitives.provenance import SourceRef
from cjm_transcript_graph_schema.schema import (AudioRenditionNode, AudioSegmentNode,
                                                SegmentNode, SourceNode,
                                                TranscriptNode, TranscriptSliceRef,
                                                audio_rendition_node_id,
                                                audio_segment_node_id,
                                                segment_node_id, source_node_id,
                                                transcript_node_id)

SID = source_node_id("sha256:abc")
A1 = audio_segment_node_id(SID, 0.0, 300.2)
R_RAW = audio_rendition_node_id(A1, [])
R_VOX = audio_rendition_node_id(A1, ["source_separation:demucs@cfg"])


def test_identity_determinism_and_cross_type_distinctness():
    assert SID == source_node_id("sha256:abc")
    assert A1 == audio_segment_node_id(SID, 0.0, 300.2)
    assert A1 != audio_segment_node_id(SID, 0.0, 300.3)
    # renditions: empty chain (raw) is stable + distinct from any preprocessing chain
    assert R_RAW == audio_rendition_node_id(A1, [])
    assert R_VOX != R_RAW, "vocals rendition is a distinct node from raw"
    assert R_RAW != A1, "the raw rendition is its own node, not the audio segment"
    assert audio_rendition_node_id(A1, ["a", "b"]) != audio_rendition_node_id(A1, ["b", "a"]), \
        "chain order matters"
    # transcript / segment key on the RENDITION now
    t1 = transcript_node_id(R_RAW, "whisper", "cfg1")
    assert t1 != transcript_node_id(R_RAW, "voxtral", "cfg1")
    assert t1 != transcript_node_id(R_RAW, "whisper", "cfg2")
    assert t1 != transcript_node_id(R_VOX, "whisper", "cfg1"), "raw vs vocals transcript distinct"
    s1 = segment_node_id(R_RAW, "vadcfg", 1.5, 4.25)
    assert s1 == segment_node_id(R_RAW, "vadcfg", 1.5, 4.25)
    assert s1 != segment_node_id(R_VOX, "vadcfg", 1.5, 4.25), "raw vs vocals fine spine distinct"
    assert len({SID, A1, R_RAW, R_VOX, t1, s1}) == 6, "kinds never collide"


def test_source_audio_segment_rendition_wire_shapes():
    src = SourceNode(content_hash="sha256:abc", path="/media/ep1.mp3")
    n = src.to_graph_node()
    assert n["label"] == "Source" and n["id"] == source_node_id("sha256:abc")
    assert n["properties"]["title"] == "ep1" and n["properties"]["root_kind"] == "ingested"
    assert n["sources"][0]["content_hash"] == "sha256:abc"
    assert SourceNode(content_hash="sha256:abc", path="/x.mp3",
                      title="Custom").to_graph_node()["properties"]["title"] == "Custom"

    # AudioSegment is a hashless boundary now (model-input moved to the rendition)
    aseg = AudioSegmentNode(source=src.id, index=0, start=0.0, end=300.2,
                            segment_path="/cuts/seg0.mp3")
    an = aseg.to_graph_node()
    assert an["id"] == audio_segment_node_id(src.id, 0.0, 300.2)
    assert an["label"] == "AudioSegment"
    assert an["properties"]["source_id"] == src.id
    assert an["properties"]["segment_path"] == "/cuts/seg0.mp3"
    assert "model_input_path" not in an["properties"], "model-input lives on the rendition now"
    assert an["sources"] == [], "boundary node is hashless"

    # AudioRendition owns the model-input; raw vs vocals coexist under one AudioSegment
    raw = AudioRenditionNode(audio_segment=aseg.id, model_input_path="/cache/seg0.wav",
                             model_input_hash="sha256:wav0")
    rn = raw.to_graph_node()
    assert rn["id"] == audio_rendition_node_id(aseg.id, []) and rn["label"] == "AudioRendition"
    assert rn["properties"]["audio_segment_id"] == aseg.id
    assert rn["properties"]["is_raw"] is True
    assert rn["properties"]["chain"] == [] and "preprocessing" not in rn["properties"]
    assert rn["sources"][0]["content_hash"] == "sha256:wav0"
    re = raw.derived_edge()
    assert re["relation_type"] == "DERIVED_FROM"
    assert re["source_id"] == rn["id"] and re["target_id"] == aseg.id

    vox = AudioRenditionNode(audio_segment=aseg.id, model_input_path="/cache/seg0_vocals.wav",
                             model_input_hash="sha256:wav0vox",
                             chain=["source_separation:demucs@cfg"])
    vn = vox.to_graph_node()
    assert vn["id"] != rn["id"], "vocals rendition coexists as a distinct node"
    assert vn["properties"]["is_raw"] is False
    assert vn["properties"]["preprocessing"] == "source_separation:demucs@cfg"
    assert vn["sources"][0]["content_hash"] == "sha256:wav0vox"


def test_transcript_shape_attribution_and_derived_edge():
    t = TranscriptNode(rendition=R_RAW, transcriber="whisper", config_hash="cfg1",
                       text="hello world", audio_hash="sha256:wav0",
                       metadata={"model": "base"}, asserted_at=123.0)
    tn = t.to_graph_node()
    assert tn["id"] == transcript_node_id(R_RAW, "whisper", "cfg1")
    assert tn["properties"]["actor"] == "capability:whisper"
    assert tn["properties"]["method"] == "transcribe"
    assert tn["properties"]["asserted_at"] == 123.0
    assert tn["properties"]["text"] == "hello world"
    assert tn["properties"]["metadata"] == {"model": "base"}
    assert tn["properties"]["rendition_id"] == R_RAW
    assert tn["sources"][0]["slice"]["kind"] == "full"
    e = t.derived_edge()
    assert e["relation_type"] == "DERIVED_FROM"
    assert e["source_id"] == tn["id"] and e["target_id"] == R_RAW
    assert e["id"] == t.derived_edge()["id"], "deterministic edge id"


def test_segment_shape_slices_identity_and_empty():
    acc = TranscriptSliceRef(transcript="t-acc", start_char=0, end_char=11, text="hello world")
    var = TranscriptSliceRef(transcript="t-lw", start_char=0, end_char=10, text="helo world")
    seg = SegmentNode(rendition=R_RAW, vad_config_hash="vadcfg", chunk_start=1.5, chunk_end=4.25,
                      index=7, start_time=101.5, end_time=104.25, text="hello world",
                      audio_hash="sha256:wav0", source=SID, text_from="t-acc",
                      text_slices=[acc, var])
    sn = seg.to_graph_node()
    assert sn["id"] == segment_node_id(R_RAW, "vadcfg", 1.5, 4.25)
    assert sn["properties"]["text"] == "hello world" and sn["properties"]["text_from"] == "t-acc"
    assert sn["properties"]["source_id"] == SID and sn["properties"]["rendition_id"] == R_RAW
    assert len(sn["sources"]) == 3
    audio_ref, acc_ref, var_ref = sn["sources"]
    assert audio_ref["slice"]["kind"] == "time" and audio_ref["slice"]["start"] == 1.5
    assert audio_ref["locator"]["node_id"] == R_RAW, "audio ref points at the rendition"
    assert acc_ref["slice"]["kind"] == "char"
    assert acc_ref["content_hash"] == SourceRef.compute_hash(b"hello world")
    assert var_ref["content_hash"] == SourceRef.compute_hash(b"helo world")

    # identity is audio-side: text changes do NOT change the id
    seg2 = SegmentNode(rendition=R_RAW, vad_config_hash="vadcfg", chunk_start=1.5, chunk_end=4.25,
                       index=7, start_time=101.5, end_time=104.25, text="different text")
    assert seg2.id == seg.id

    # empty (D14-class) segment: audio ref only, no text_from
    empty = SegmentNode(rendition=R_RAW, vad_config_hash="vadcfg", chunk_start=9.0, chunk_end=9.5,
                        index=8, start_time=109.0, end_time=109.5, audio_hash="sha256:wav0")
    en = empty.to_graph_node()
    assert en["properties"]["text"] == "" and "text_from" not in en["properties"]
    assert len(en["sources"]) == 1
