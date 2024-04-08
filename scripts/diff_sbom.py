# Copyright 2023 Lawrence Livermore National Security, LLC
# See the top-level LICENSE file for details.
#
# SPDX-License-Identifier: MIT

from argparse import ArgumentParser
from pathlib import Path

from surfactant.plugin.manager import find_io_plugin, get_plugin_manager

# Process:
# - We will open both SBOMS
# - For each SBOM we will build a path list
# - We will iterate in the path list, if an entry does not exist we will note it
#  - If the hash differs we will note it (potentially allow for different comparision metric later.)


def parse_args():
    parser = ArgumentParser()
    parser.add_argument("sbomA")
    parser.add_argument("sbomB")
    return parser.parse_args()

def main(_args):

    pm = get_plugin_manager()

    input_reader = find_io_plugin(pm, "surfactant.input_readers.cytrics_reader", "read_sbom")
    with open(_args.sbomA) as f:
        sbomA = input_reader.read_sbom(f)
    with open(_args.sbomB) as f:
        sbomB = input_reader.read_sbom(f)

    diff(sbomA, sbomB, compare_by_sha256)

def compare_by_sha256(software_a, software_b):
    values = software_a.sha256, software_b.sha256
    return software_a.sha256 == software_b.sha256, "SHA256", values

def diff(sbomA, sbomB, compare_func):
    software_by_pathes = {}

    for software in sbomA.software:
        for path in software.installPath:
            p = Path(path)
            software_by_pathes[p] = (software, None)

    for software in sbomB.software:
        for path in software.installPath:
            p = Path(path)
            if p in software_by_pathes:
                software_by_pathes[p] = (software_by_pathes[p][0], software)
            else:
                software_by_pathes[p] = (None, software)

    software_by_pathes = dict(sorted(software_by_pathes.items()))
    for path, (software_a, software_b) in software_by_pathes.items():
        if software_b and software_a is not None:
            compare_result, key, values = compare_func(software_a, software_b)
            if not compare_result:
                print(f"{path}:")
                print(f"    < {key}: {values[0]}")
                print(f"    > {key}: {values[1]}")
                print()
        else:
            print(f"{path}:")
            print(f"    < {'EXISTS' if software_a is not None else 'DOES NOT EXIST'}")
            print(f"    > {'EXISTS' if software_b is not None else 'DOES NOT EXIST'}")
            print()

if __name__ == "__main__":
    args = parse_args()
    main(args)
