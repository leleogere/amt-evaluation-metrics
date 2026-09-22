import logging

import tqdm
import joblib
from tqdm import tqdm
from pathlib import Path


class Metric:
    def __init__(self, depends_on_music21: bool):
        self.logger = logging.getLogger(self.name())
        self.depends_on_music21 = depends_on_music21

    @classmethod
    def name(cls) -> str:
        return cls.__name__

    @classmethod
    def prefix(cls) -> str:
        return cls.name()

    def batch_compute(self, est: list[Path], ref: list[Path], n_jobs: int = 1):
        if len(est) != len(ref):
            raise ValueError("Est and ref must have the same length")
        n = len(est)
        if n_jobs == 1:
            metrics = [self.compute(est=e, ref=r) for e, r in tqdm(zip(est, ref), total=n)]
        else:
            metrics = [
                m
                for m in tqdm(
                    joblib.Parallel(n_jobs=n_jobs, return_as="generator", backend="threading")(
                        joblib.delayed(self.compute)(e, r) for e, r in zip(est, ref)
                    ),
                    total=n,
                )
            ]
        return metrics

    def self_batch_compute(self, scores: list[Path], n_jobs: int = 1):
        return self.batch_compute(est=scores, ref=scores, n_jobs=n_jobs)

    def compute(self, est: Path, ref: Path) -> dict[str, float | int | None]: ...

    @classmethod
    def all_metrics(cls) -> list[str]: ...

    @classmethod
    def studied_metrics(self) -> list[str]:
        return self.all_metrics()

    def return_error(
        self, override: dict[str, float | int | None] | None = None
    ) -> dict[str, float | int | None]:
        d = {k: None for k in self.all_metrics()}
        if override is not None:
            d.update(override)
        return d

    @staticmethod
    def metric_to_test_for_error(): ...
