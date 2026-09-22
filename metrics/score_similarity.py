from pathlib import Path

from metrics.base import Metric


class ScoreSimilarity(Metric):
    def __init__(self):
        super().__init__(depends_on_music21=True)
        self._m21_version_logged = False

    @classmethod
    def prefix(cls) -> str:
        return "SS"

    def _import_score_similarity(self):
        from ScoreTransformer.metric.ScoreSimilarity import scoreSimilarity  # fmt: skip
        return scoreSimilarity

    def compute(self, est: Path, ref: Path) -> dict[str, float | int | None]:
        # Delay the import to load the correct music21 version
        scoreSimilarity = self._import_score_similarity()
        import music21

        if not self._m21_version_logged:
            self.logger.info(f"Using music21 version {music21.__version__}")
            self._m21_version_logged = True

        try:
            est_score = music21.converter.parse(est)
            ref_score = music21.converter.parse(ref)
        except Exception as e:
            self.logger.error(f"Error parsing score: {e}")
            return self.return_error()

        try:
            unnormalized_results = scoreSimilarity(estScore=est_score, gtScore=ref_score)
            return self._normalize_metrics(unnormalized_results)
        except Exception as e:
            self.logger.error(f"Error computing {self.name()} metric: {e}")
            return self.return_error()

    def _normalize_metrics(
        self, metrics: dict[str, float | int | None]
    ) -> dict[str, float | int | None]:
        norm_metrics = {k: v for k, v in metrics.items()}
        for n_symbols, metrics_to_normalize in self._metrics_to_normalize().items():
            factor = sum([metrics.get(n, 0) for n in n_symbols])
            for m in metrics_to_normalize:
                norm_metrics[m] = (
                    (norm_metrics[m] / factor) * 100
                    if ((factor != 0) and (norm_metrics[m] is not None))
                    else None
                )
        return norm_metrics

    @staticmethod
    def _metrics_to_normalize() -> dict[tuple[str, ...], list[str]]:
        return {
            ("n_Note", "n_Chord"): [
                "NoteDeletion",
                "NoteInsertion",
                "NoteSpelling",
                "NoteDuration",
                "StemDirection",
                "Beams",
                "Tie",
                "StaffAssignment",
                "Voice",
            ],
            ("n_Rest",): [
                "RestDeletion",
                "RestInsertion",
                "RestDuration",
            ],
        }

    @classmethod
    def all_metrics(cls) -> list[str]:
        return [
            "Clef",
            "KeySignature",
            "TimeSignature",
            "NoteDeletion",
            "NoteInsertion",
            "NoteSpelling",
            "NoteDuration",
            "StemDirection",
            "Beams",
            "Tie",
            "RestInsertion",
            "RestDeletion",
            "RestDuration",
            "StaffAssignment",
            "Voice",
            "n_Note",
            "n_Chord",
            "n_Rest",
        ]

    @classmethod
    def studied_metrics(cls) -> list[str]:
        return [
            "NoteInsertion",
            "NoteDeletion",
            "NoteDuration",
            "NoteSpelling",
            "Tie",
            "StaffAssignment",
            "Voice",
            "StemDirection",
        ]

    @staticmethod
    def metric_to_test_for_error():
        return "NoteInsertion"


class ScoreSimilarityBeyer(ScoreSimilarity):
    @classmethod
    def prefix(cls) -> str:
        return "SSb"

    def _import_score_similarity(self):
        from ScoreTransformerB.score_transformer_b.metric.ScoreSimilarity import score_similarity  # fmt: skip
        return score_similarity

    @staticmethod
    def _metrics_to_normalize() -> dict[tuple[str, ...], list[str]]:
        return {
            ("n_Note",): [
                "Clef",
                "KeySignature",
                "TimeSignature",
                "NoteDeletion",
                "NoteInsertion",
                "NoteSpelling",
                "NoteDuration",
                "StemDirection",
                "Beams",
                "Tie",
                "StaffAssignment",
                "Voice",
            ]
        }

    def all_metrics(cls) -> list[str]:
        return [
            "Clef",
            "KeySignature",
            "TimeSignature",
            "NoteDeletion",
            "NoteInsertion",
            "NoteSpelling",
            "NoteDuration",
            "StemDirection",
            "Beams",
            "Tie",
            "StaffAssignment",
            "Voice",
            "TrillTP",
            "TrillFP",
            "TrillTN",
            "TrillFN",
            "StaccatoTP",
            "StaccatoFP",
            "StaccatoTN",
            "StaccatoFN",
            "GraceTP",
            "GraceFP",
            "GraceTN",
            "GraceFN",
            "TrillPrec",
            "TrillRec",
            "TrillF1",
            "StaccatoPrec",
            "StaccatoRec",
            "StaccatoF1",
            "GracePrec",
            "GraceRec",
            "GraceF1",
            "n_Note",
        ]

    def studied_metrics(cls) -> list[str]:
        return [
            "NoteInsertion",
            "NoteDeletion",
            "NoteDuration",
            "NoteSpelling",
            "StemDirection",
            "TrillF1",
            "StaccatoF1",
            "GraceF1",
        ]
