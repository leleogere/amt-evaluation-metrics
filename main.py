import itertools
import re
import sys
from pathlib import Path
from typing import Callable

import click
import joblib
import pandas as pd
import tqdm
from tqdm import tqdm
import matplotlib.pyplot as plt
import logging

from metrics.muster import MusterClean, MusterNotClean
from metrics.mv2h import MV2H
from metrics.score_similarity import ScoreSimilarity, ScoreSimilarityBeyer
from package_switcher import PackageAliasFinder

# Set pandas options
pd.set_option("display.max_columns", None)
pd.set_option("display.max_rows", None)
pd.set_option("display.width", 10000)


# fmt: off
@click.command()
@click.argument("dataset_path", type=click.Path(exists=True, readable=True, path_type=Path))
@click.option("--score-file-pattern", type=str, default=r"^xml_score\.(musicxml|mxl)$", help="Regex pattern used to gather all files in the dataset.")
@click.option("--transcription-file-pattern", type=str, help="Regex pattern of a transcription file, that should lie in the same directory as the corresponding score file. If not provided, simply run a self-comparison test (each score of the dataset against itself).")
@click.option("--metrics", "-m", type=click.Choice(prefix_to_metric.keys()), multiple=True, required=True, help="Metrics to compute. Pass the option multiple times to compute multiple metrics.")
@click.option("--output-directory", "-o", type=click.Path(writable=True, path_type=Path), help="Directory where to save the output CSV and log files, dataset_path if not specified.")
@click.option("--limit", "-l", type=int, default=None, help="Limit the number of scores to compute. Useful for debugging.")
@click.option("--n-jobs", "-j", type=int, default=1, help="Number of jobs to use for parallel computation (using threading for easier music21 library swapping, see next option). Note that some metrics like ScoreSimilarity seem to prefer 1.")
@click.option("--beyer-music21", "-b", is_flag=True, help="Use Beyer's music21 version instead of the default one, only use full for metrics relying on it.")
# fmt: on
def main(
    dataset_path: Path,
    score_file_pattern: str,
    metrics: tuple[str],
    output_directory: Path | None = None,
    transcription_file_pattern: str | None = None,
    limit: int | None = None,
    n_jobs: int = 1,
    beyer_music21: bool = False,
):
    # Import correct music21 version, and load muster AFTER it
    if beyer_music21:
        sys.meta_path.insert(0, PackageAliasFinder("music21", "music21b"))
        from music21 import __version__  # fmt: skip
        m21version = "beyer." + __version__
    else:
        from music21 import __version__  # fmt: skip
        m21version = __version__

    # Setup output directory
    if output_directory is None:
        output_directory = dataset_path
    output_directory.mkdir(parents=True, exist_ok=True)
    print(output_directory)

    for prefix in metrics:
        metric = prefix_to_metric[prefix]()

        print("\n\n" + "#" * 80)
        print(f"Computing metric {metric.name()} for {dataset_path}")

        # Setup output paths
        output_components = [metric.name()]
        if transcription_file_pattern is not None:
            output_components.append("transcription")
        if limit is not None:
            output_components.append(f"limit={limit}")
        if metric.depends_on_music21:
            output_components.append(f"music21={m21version}")
        output_csv = output_directory / ("_".join(output_components) + ".csv")
        output_log = output_csv.with_suffix(".log")

        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(message)s",
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler(output_log, mode="w"),
            ],
            force=True,
        )
        logger = logging.getLogger(metric.name())
        print(f"{logger.name} logging to {output_log.as_posix()}")
        logger.info(f"Using music21 version {m21version}")

        if not output_csv.exists():
            # Load scores
            scores = sorted(
                list(
                    itertools.chain(
                        f for f in dataset_path.rglob("*.*") if re.match(score_file_pattern, f.name)
                    )
                )
            )
            logger.info(f"Loaded {len(scores)} scores")

            # Load transcriptions
            if transcription_file_pattern is not None:
                logger.info(f"Using transcription file pattern {transcription_file_pattern}")
                transcriptions = [
                    next(
                        (
                            f
                            for f in s.parent.rglob("*.*")
                            if re.match(transcription_file_pattern, f.name)
                        ),
                        None,
                    )
                    for s in scores
                ]
                successful_transcriptions = [t for t in transcriptions if t is not None]
                if len(set(successful_transcriptions)) != len(successful_transcriptions):
                    raise ValueError(
                        f"Duplicated transcription files found matching "
                        f"{transcription_file_pattern}. Make sure that the pattern only matches "
                        f"a single transcription per score."
                    )
                # Filter out failed transcriptions:
                indices_to_remove = []
                for i, (s, t) in enumerate(zip(scores, transcriptions)):
                    if t is None:
                        logger.warning(f"No transcription for {s}, skipping it.")
                        indices_to_remove.append(i)
                if len(indices_to_remove) > 0:
                    scores = [s for i, s in enumerate(scores) if i not in indices_to_remove]
                    transcriptions = [
                        t for i, t in enumerate(transcriptions) if i not in indices_to_remove
                    ]
                    logger.warning(f"Removed {len(indices_to_remove)} failed transcriptions.")

            else:
                transcriptions = scores

            # Limit dataset if required
            if limit is not None:
                scores = scores[:limit]
                transcriptions = transcriptions[:limit]

            # Compute metrics
            results = metric.batch_compute(
                est=transcriptions,
                ref=scores,
                n_jobs=n_jobs,
            )

            # Create dataframe
            df = pd.DataFrame(
                results, index=[p.relative_to(dataset_path).as_posix() for p in scores]
            )

            # Save dataframe to CSV
            df.to_csv(output_csv, index=True)
        else:
            df = pd.read_csv(output_csv, index_col=0)
            logger.info(f"Loading {metric.name()} for {len(df)} scores from {output_csv}")

        # Export rank
        # if not (any("_rank" in col for col in df.columns)):
        #     rank = df.rank(axis=0, method="first")
        #     rank.columns = [f"{col}_rank" for col in rank.columns]
        #     df = pd.concat([df, rank], axis=1)
        #     df.to_csv(output_csv)

        # Count number of errors (at least one NaN on the line)
        errors = df[df[metric.metric_to_test_for_error()].isna()].index.tolist()
        logger.info("#" * 80)
        logger.info(f"Number of errors: {len(errors)}")
        for file in errors:
            logger.info(f"  - {file}")

        # Compute average of all metrics
        logger.info("#" * 80)
        logger.info(f"Average metrics:")
        logger.info(df[[c for c in df.columns if "_rank" not in c]].mean())

        # Print summary
        logger.info("#" * 80)
        logger.info(f"Summary:")
        logger.info(df[metric.studied_metrics()].describe())

        # Print boxplots for those metrics
        # plotted_metrics = ["ExtraRate", "MissRate", "PitchER", "OnsetER", "OffsetER", "MeanER"]
        # plt.figure(figsize=(12, 8))
        # for metric in plotted_metrics:
        #     plt.subplot(2, 3, plotted_metrics.index(metric) + 1)
        #     plt.title(metric)
        #     plt.boxplot(df[metric][~df[metric].isna()].values)
        # plt.tight_layout()
        # plt.show()

        # Get top k highest and lowest scores for each metric
        k = 5
        logger.info("#" * 80)
        logger.info(f"Top {k} scores:")
        for m in metric.studied_metrics():
            logger.info(m)
            for path, score in df[m].nlargest(k).items():
                logger.info(f"  - {score:.3f} - {path}")
            logger.info("    ...")
            for path, score in df[m].nsmallest(k).iloc[::-1].items():
                logger.info(f"  - {score:.3f} - {path}")
            logger.info("")

        logger.info("")


if __name__ == "__main__":
    main()
