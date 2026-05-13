from uhskd.delta.processor import DeltaConfig, DeltaProcessor
from uhskd.knowledge_vault.base import InMemoryKnowledgeVault
from uhskd.models import DeltaLabel, TranscriptSegment, VaultRecord


class StubCrossEncoder:
    def predict(self, pairs):
        scores = []
        for query, _document in pairs:
            if "redundante" in query:
                scores.append(0.9)
            elif "matiz" in query:
                scores.append(0.5)
            else:
                scores.append(0.1)
        return scores


def test_delta_classification_labels():
    vault = InMemoryKnowledgeVault()
    vault.upsert([VaultRecord(identifier="1", text="conocimiento base", metadata={})])

    processor = DeltaProcessor(
        vault,
        DeltaConfig(
            novelty_similarity_threshold=0.2,
            reinforcement_similarity_threshold=0.6,
            min_characters=10,
            min_confidence=0.1,
        ),
        cross_encoder=StubCrossEncoder(),
    )

    novelty_segment = TranscriptSegment(
        text="una idea completamente nueva para el repositorio",
        start_s=0.0,
        end_s=1.0,
        confidence=0.9,
    )
    nuance_segment = TranscriptSegment(
        text="este segmento aporta un matiz sobre el conocimiento base",
        start_s=2.0,
        end_s=3.0,
        confidence=0.9,
    )
    redundant_segment = TranscriptSegment(
        text="contenido redundante del conocimiento base",
        start_s=3.1,
        end_s=4.0,
        confidence=0.9,
    )
    noise_segment = TranscriptSegment(
        text="corto",
        start_s=4.1,
        end_s=4.3,
        confidence=0.9,
    )

    novelty_result = processor.classify_segment(novelty_segment)
    nuance_result = processor.classify_segment(nuance_segment)
    redundant_result = processor.classify_segment(redundant_segment)
    noise_result = processor.classify_segment(noise_segment)

    assert novelty_result.label is DeltaLabel.NOVEDAD_ABSOLUTA
    assert nuance_result.label is DeltaLabel.MATIZ_REFUERZO
    assert redundant_result.label is DeltaLabel.REDUNDANTE
    assert noise_result.label is DeltaLabel.RUIDO
