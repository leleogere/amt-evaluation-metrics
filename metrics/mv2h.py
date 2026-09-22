import select
import sys

import re
from pathlib import Path

import subprocess

from metrics.base import Metric


class MV2H(Metric):
    def __init__(
        self,
        mscore_exe: str | Path = "mscore4portable",
        mv2h_bin: Path = Path("./MV2H/bin"),
        alignment_error_threshold: int = int(1e4),
    ):
        super().__init__(depends_on_music21=False)
        self.mscore_exe = mscore_exe
        self.mv2h_bin = mv2h_bin
        self.alignment_error_threshold = alignment_error_threshold

    @classmethod
    def prefix(cls) -> str:
        return "MV2H"

    def _musicxml_to_mid(self, input_musicxml: Path, output_mid: Path, timeout: int = 20):
        # mscore4portable -f -o output.mid input.musicxml
        process = subprocess.run(
            [self.mscore_exe, "-f", "-o", output_mid, str(input_musicxml)],
            timeout=timeout,
        )
        if process.returncode != 0:
            raise Exception(
                f"mscore4portable failed with error code {process.returncode}: {process.stderr}"
            )

    def _mid_to_txt(self, input_mid: Path, output_txt: Path, timeout: int = 20):
        # java -cp bin mv2h.tools.Converter -i input.mid -o output.txt
        process = subprocess.run(
            ["java", "-cp", str(self.mv2h_bin), "mv2h.tools.Converter", "-i", str(input_mid), "-o", str(output_txt)],  # fmt: skip
            timeout=timeout,
        )
        if process.returncode != 0:
            raise Exception(
                f"mv2h.tools.Converter failed with error code {process.returncode}: {process.stderr}"
            )

    def _metric_compute(self, est_txt: Path, ref_txt: Path, timeout: int = 120) -> dict[str, float]:
        # java -cp bin mv2h.Main -g ref.txt -t est.txt -a
        # Here, we don't use subprocess.run as we want to detect if the alignment process has
        # issues, i.e. produces things like  "Evaluating alignment i / 147740585775889121280"
        process = subprocess.Popen(
            ["java", "-cp", str(self.mv2h_bin), "mv2h.Main", "-g", str(ref_txt), "-t", str(est_txt), "-a"],  # fmt: skip
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )

        # Search for the alignment total n, in stdout under the form "Evaluating alignment i / n"
        alignment_pattern = re.compile(r"Evaluating alignment \d+ / (\d+)")
        buffer = ""
        full_stdout = ""
        num_alignments = None
        while True:
            # If num_alignments already found, stop searching, simply store the stream
            if num_alignments is not None:
                char = process.stdout.read(1)
                if not char:
                    break
                full_stdout += char
                continue

            # Use select to wait for output with a short timeout (50ms)
            reads, _, _ = select.select([process.stdout], [], [], 0.05)

            if process.stdout in reads:
                char = process.stdout.read(1)
                if not char:
                    break

                buffer += char
                full_stdout += char

                # If we hit a newline or carriage return, check the buffer and clear it
                if char == "\r" or char == "\n":
                    match = alignment_pattern.search(buffer)
                    if match:
                        num_alignments = int(match.group(1))
                        if num_alignments > self.alignment_error_threshold:
                            process.terminate()
                            raise Exception(
                                f"Total alignments exceed the threshold: "
                                f"{num_alignments} > {self.alignment_error_threshold}",
                                num_alignments,
                            )
                    buffer = ""
            else:
                # Timeout reached, meaning the output has paused
                # We can now safely check the buffer for the complete number
                match = alignment_pattern.search(buffer)
                if match:
                    num_alignments = int(match.group(1))
                    if num_alignments > self.alignment_error_threshold:
                        process.terminate()
                        raise Exception(
                            f"Total alignments exceed the threshold: "
                            f"{num_alignments} > {self.alignment_error_threshold}",
                            num_alignments,
                        )

        process.communicate(timeout=timeout)
        if process.returncode != 0:
            raise Exception(f"mv2h.Main failed with error code {process.returncode}")
        parsed_stdout = [("Alignments", num_alignments)] + [
            tuple(l.split(": "))
            for l in full_stdout.splitlines()
            if l != "" and not l.startswith("Evaluating alignment")
        ]
        return {k: (float(v) if isinstance(v, str) else v) for k, v in parsed_stdout}

    def compute(self, est: Path, ref: Path) -> dict[str, float | int | None]:
        # Convert the scores to MIDI
        midi_est, midi_ref = est.with_suffix(".mv2h.mid"), ref.with_suffix(".mv2h.mid")
        try:
            self._musicxml_to_mid(est, midi_est)
            if est != ref:  # Skip if same file
                self._musicxml_to_mid(ref, midi_ref)
        except Exception as e:
            self.logger.error(f"Error converting score to MIDI: {e}")
            if midi_est.exists(): midi_est.unlink()  # fmt: skip
            if midi_ref.exists(): midi_ref.unlink()  # fmt: skip
            return self.return_error()

        # Convert to MV2H format
        txt_est, txt_ref = midi_est.with_suffix(".txt"), midi_ref.with_suffix(".txt")
        try:
            self._mid_to_txt(midi_est, txt_est)
            if est != ref:  # Skip if same file
                self._mid_to_txt(midi_ref, txt_ref)
        except Exception as e:
            self.logger.error(f"Error converting MIDI to MV2H format: {e}")
            return self.return_error()
        finally:
            if midi_est.exists(): midi_est.unlink()  # fmt: skip
            if midi_ref.exists(): midi_ref.unlink()  # fmt: skip

        # Compute metrics
        try:
            return self._metric_compute(txt_est, txt_ref)
        except Exception as e:
            if len(e.args) == 2:
                message, num_alignments = e.args
                self.logger.error(f"Error computing MV2H metrics: {message}")
                return self.return_error({"Alignments": num_alignments})
            else:
                self.logger.error(f"Error computing MV2H metrics: {e}")
                return self.return_error()
        finally:
            if txt_est.exists(): txt_est.unlink()  # fmt: skip
            if txt_est.exists(): txt_ref.unlink()  # fmt: skip

    @classmethod
    def all_metrics(cls) -> list[str]:
        return [
            "Alignments",
            "Multi-pitch",
            "Voice",
            "Meter",
            "Value",
            "Harmony",
            "MV2H",
        ]

    @classmethod
    def studied_metrics(cls) -> list[str]:
        return [
            "Multi-pitch",
            "Voice",
            "Meter",
            "Value",
            "Harmony",
            "MV2H",
        ]

    @staticmethod
    def metric_to_test_for_error():
        return "MV2H"
