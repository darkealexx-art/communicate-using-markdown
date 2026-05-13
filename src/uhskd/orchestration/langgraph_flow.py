from __future__ import annotations

from typing import TypedDict

from uhskd.delta.processor import DeltaProcessor
from uhskd.models import DeltaResult, IngestItem, Transcript
from uhskd.output.markdown import MarkdownOutputGenerator
from uhskd.transcription import Transcriber


class PipelineState(TypedDict):
    item: IngestItem
    transcript: Transcript | None
    results: list[DeltaResult]
    output_path: str | None


def build_langgraph_flow(
    transcriber: Transcriber,
    delta_processor: DeltaProcessor,
    output_generator: MarkdownOutputGenerator | None = None,
):
    try:
        from langgraph.graph import StateGraph
    except ModuleNotFoundError as exc:
        raise RuntimeError("langgraph is required for orchestration") from exc

    graph = StateGraph(PipelineState)

    def transcribe_node(state: PipelineState) -> PipelineState:
        transcript = transcriber.transcribe(state["item"])
        return {**state, "transcript": transcript}

    def delta_node(state: PipelineState) -> PipelineState:
        transcript = state["transcript"]
        if transcript is None:
            return {**state, "results": []}
        results = list(delta_processor.process_transcript(transcript))
        delta_processor.index_results(results)
        return {**state, "results": results}

    def output_node(state: PipelineState) -> PipelineState:
        if output_generator is None or state["transcript"] is None:
            return state
        title = state["item"].metadata.get("title") or state["item"].local_path.stem
        path = output_generator.write_markdown(state["transcript"], state["results"], str(title))
        return {**state, "output_path": str(path)}

    graph.add_node("transcribe", transcribe_node)
    graph.add_node("delta", delta_node)
    graph.add_node("output", output_node)

    graph.set_entry_point("transcribe")
    graph.add_edge("transcribe", "delta")
    graph.add_edge("delta", "output")
    graph.set_finish_point("output")

    return graph.compile()
