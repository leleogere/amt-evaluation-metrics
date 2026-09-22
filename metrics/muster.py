from pathlib import Path


from metrics.base import Metric


class Muster(Metric):
    def __init__(self, clean_scores: bool = False):
        self.clean_scores = clean_scores
        self._m21_version_logged = False
        super().__init__(depends_on_music21=(self.clean_scores == True))

    @classmethod
    def prefix(cls) -> str:
        return "MU"

    def compute(self, est: Path, ref: Path) -> dict[str, float | int | None]:
        # Delay the import to load the correct music21 version
        from muster import muster

        if not self._m21_version_logged:
            from music21 import __version__

            self.logger.info(f"Using music21 version {__version__}")
            self._m21_version_logged = True

        try:
            return muster(score_est=est, score_gt=ref, clean_scores=self.clean_scores)
        except Exception as e:
            self.logger.error(f"Error computing {self.name()} metric: {e}")
            return self.return_error()

    @classmethod
    def all_metrics(cls) -> list[str]:
        return [
            "ExtraRate",
            "MissRate",
            "PitchER",
            "OnsetER",
            "OffsetER",
            "MeanER",
            "VoiceER",
            "NewMeanER",
            "Pvoi",
            "Rvoi",
            "Fvoi",
            "ScaleErr",
            "HandER",
        ]

    @classmethod
    def studied_metrics(cls) -> list[str]:
        return [
            "ExtraRate",
            "MissRate",
            "PitchER",
            "OnsetER",
            "OffsetER",
            "MeanER",
        ]

    @staticmethod
    def metric_to_test_for_error():
        return "ExtraRate"


class MusterClean(Muster):
    def __init__(self):
        super().__init__(clean_scores=True)

    @classmethod
    def prefix(cls) -> str:
        return "MUc"


class MusterNotClean(Muster):
    def __init__(self):
        super().__init__(clean_scores=False)

    @classmethod
    def prefix(cls) -> str:
        return "MUnc"
