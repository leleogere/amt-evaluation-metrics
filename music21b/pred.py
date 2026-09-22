import pretty_midi
from collections import Counter
from music21b import converter, stream
from music21b.midi.translate import prepareStreamForMidi
import os
import matplotlib.pyplot as plt
from joblib import Parallel, delayed
import numpy as np

# TODO: PAIR EVERYTHING WITH MUSESCORE GENERATED GT SINCE music21's quantization is not good
# with open("quantize_.log", "r") as f:
#     l = f.readlines()


# substs = {}
# for line in l:
#     o, n = line.split("->")
#     if "/" in o:
#         num, denom = o.split("/")
#         o = float(num) / float(denom)
#     if "/" in n:
#         num, denom = n.split("/")
#         n = float(num) / float(denom)
#     # o = int(float(o) * 100000) / 100000 % 4
#     o = int(float(o) * 480) % (480)
#     n = ""# n = int(float(n) * 100000) / 100000 % 4
#     if (o, n) not in substs:
#         substs[(o, n)] = 0
#     substs[(o, n)] += 1
# keys = sorted(list(substs.keys()))
# for key in keys:
#     print((*key, substs[key]))
# plt.scatter([k[0] for k in keys], [substs[key] for key in keys], s=2)
# plt.yscale("log")
# plt.vlines([0, 120, 240, 360, 480], 1, 10**6, colors='g', linestyles="dotted")
# plt.vlines([160, 320], 1, 10**6, colors="r", linestyles="dotted")
# plt.savefig("quantize.png")
# plt.close()
def process_file(path):
    print(path)
    m = converter.parse(path, quantizePost=False)
    m.quantize((8, 3), recurse=True)
    m = prepareStreamForMidi(m)
    # lengths = []
    # for n in m.flat.notes:
    #     lengths.append(n.duration.quarterLength)
    # c = Counter(lengths)
    # plt.hist(lengths, bins=100)
    # plt.savefig(f"test{path.replace('/','_')}.png")
    # plt.close()
    # mid = pretty_midi.PrettyMIDI(path)
    # new_mid = pretty_midi.PrettyMIDI()
    # new_instrument = pretty_midi.Instrument(0)
    # for instrument in mid.instruments:
    #     for n in instrument.notes:
    #         new_instrument.notes.append(pretty_midi.Note(n.velocity, n.pitch, n.start, n.start + 0.021))
    # new_mid.instruments.append(new_instrument)
    # c = Counter((new_mid.get_piano_roll(fs=1000, pedal_threshold=None) > 0).sum(0).astype(int).tolist())
    c = Counter([0])
    return c


paths = []
for root, dirs, files in os.walk(
    "/Volumes/Macintosh HD (SATA)/Users/Tim/Documents/thesis/data"
):
    for file in files:
        if file.endswith(".mid"):
            paths.append(os.path.join(root, file))
import time

t0 = time.time()
counts = [process_file(path) for path in paths]
t1 = time.time()
print(t1 - t0)

# counts = Parallel(n_jobs=8)(delayed(process_file)(path) for path in paths)
# merged_counter = Counter()

# loop through the list of counters and update the new counter
# for counter in counts:
#     merged_counter.update(counter)
# del merged_counter[0]

# total = np.sum(list(merged_counter.values()))
# x = sorted(merged_counter.keys())
# y = [merged_counter[key] / total for key in x]
# plt.scatter(x, y, s=1)
# plt.plot(x, np.cumsum(y))


# plt.xlabel("Number of notes")
# plt.ylabel("Number of songs")
# plt.savefig("histogram.png")
# print(merged_counter, np.cumsum(y))
