from uhskd.delta.processor import DeltaConfig, DeltaLogicProcessor
from uhskd.knowledge_vault.base import InMemoryKnowledgeVault
from uhskd.models import DeltaLabel, TranscriptSegment, VaultRecord


def test_delta_classification_labels():
    vault = InMemoryKnowledgeVault()
    vault.upsert([VaultRecord(identifier="1", text="conocimiento base", metadata={})])

    processor = DeltaLogicProcessor(
        vault,
        DeltaConfig(
            novelty_similarity_threshold=0.2,
            reinforcement_similarity_threshold=0.6,
            min_characters=10,
            min_confidence=0.1,
        ),
    )

    novelty_segment = TranscriptSegment(
        text="una idea completamente nueva para el repositorio",
        start_s=0.0,
        end_s=1.0,
        confidence=0.9,
    )
    reinforce_segment = TranscriptSegment(
        text="este segmento refuerza el conocimiento base",
        start_s=2.0,
        end_s=3.0,
        confidence=0.9,
    )
    noise_segment = TranscriptSegment(
        text="corto",
        start_s=4.0,
        end_s=4.2,
        confidence=0.9,
    )

    novelty_result = processor.classify_segment(novelty_segment)
    reinforce_result = processor.classify_segment(reinforce_segment)
    noise_result = processor.classify_segment(noise_segment)

    assert novelty_result.label is DeltaLabel.NOVEDAD
    assert reinforce_result.label is DeltaLabel.REFUERZO
    assert noise_result.label is DeltaLabel.RUIDO
