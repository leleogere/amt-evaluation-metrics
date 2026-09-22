# AMT metrics evaluation

This repository contains some script to evaluate three popular Automatic Music Transcription (AMT) evaluation metrics.

## Metrics included

Note that some metrics are implemented differently by different papers.
  - MUSTER
    - Both [original version](https://github.com/amtevaluation/amtevaluation.github.io) and [Beyer version](https://github.com/TimFelixBeyer/amtevaluation.github.io)
  - ScoreSimilarity
    - Both [Suzuki version](https://github.com/suzuqn/ScoreTransformer) and [Beyer version](https://github.com/TimFelixBeyer/ScoreTransformer)
  - MV2H ([McLeod](https://github.com/apmcleod/MV2H))

Due to issues in different versions, some unusual tricks are required to ensure that the correct version of each metric and its dependencies.
I am not familiar enough with Python's import mecanism to guarantee that those will always work in the future, but hopefully `uv` will take care of that.

## Tests available

Two tests are available:
  - Self-similarity test: compare a score with itself, ensuring that the metric behaves as expected in this case (error of zero, or similarity of one).
  - Real transcription test: compute the metric on a real transcription task (need an already transcribed dataset).

## Usage

The script can be run with `uv`: `uv run python main.py`.
The full usage can be seen with `--help`:

```txt
Usage: main.py [OPTIONS] DATASET_PATH

Options:
  --score-file-pattern TEXT       Regex pattern used to gather all files in
                                  the dataset.
  --transcription-file-pattern TEXT
                                  Regex pattern of a transcription file, that
                                  should lie in the same directory as the
                                  corresponding score file. If not provided,
                                  simply run a self-comparison test (each
                                  score of the dataset against itself).
  -m, --metrics [MUc|MUnc|SS|SSb|MV2H]
                                  Metrics to compute. Pass the option multiple
                                  times to compute multiple metrics.
                                  [required]
  -o, --output-directory PATH     Directory where to save the output CSV and
                                  log files, dataset_path if not specified.
  -l, --limit INTEGER             Limit the number of scores to compute.
                                  Useful for debugging.
  -j, --n-jobs INTEGER            Number of jobs to use for parallel
                                  computation (using threading for easier
                                  music21 library swapping, see next option).
                                  Note that some metrics like ScoreSimilarity
                                  seem to prefer 1.
  -b, --beyer-music21             Use Beyer's music21 version instead of the
                                  default one, only use full for metrics
                                  relying on it.
  --help                          Show this message and exit.
```

### Self-similarity

```bash
uv run python main.py "$HOME/datasets/asap-dataset" -m MUnc --score-file-pattern "^original.musicxml$"
```

The available metrics `-m` are:
  - `MUc`: MUSTER with `clean_scores=True` (only used for Beyer's version, when `-b` is passed, else identical to `MUnc`)
  - `MUnc`: MUSTER with `clean_scores=False` (only used for Beyer's version, when `-b` is passed, else identical to `MUc`)
  - `SS`: ScoreSimilarity (Suzuki's version)
  - `SSb`: ScoreSimilarity (Beyer's version, only use with `-b` to also get the Beyer's version of `music21`)
  - `MV2H`: MV2H

The flag `-b` load the Beyer's version of the library `music21`.
It is only useful for Beyer's ScoreSimilarity (`SSb`) and MUSTER (`MUc` and `MUnc`).
MV2H does not use `music21` so it won't make a difference.

### Real transcription

```bash
uv run python main.py "$HOME/datasets/asap-dataset-transcribed" -m MUnc --score-file-pattern "^original.musicxml$" --transcription-file-pattern "^transcription.musicxml$"
```
