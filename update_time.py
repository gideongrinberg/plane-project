#! /usr/bin/env python3

import re
import pathlib
import datetime
import subprocess

journal = (pathlib.Path(__file__).resolve().parent / "JOURNAL.md").resolve().as_posix()
regex = re.compile(r"Time spent: ([\d](?:[\.\d])*)+hr")

with open(journal, "r") as f:
    lines = f.readlines()

total_line = -1
total_time = 0
for i, line in enumerate(lines):
    if line.startswith("Total time"):
        total_line = i
    
    if line.startswith("Time spent"):
        time = regex.findall(line)[0]
        total_time += float(time)

now = datetime.datetime.now()
lines[total_line] = f"Total time spent as of {now.strftime("%B %d")}: {int(total_time)} hours and {int(round((total_time - int(total_time)) * 60))} minutes\n"
with open(journal, "w") as f:
    f.write("".join(lines))

subprocess.run(["git", "add", journal])