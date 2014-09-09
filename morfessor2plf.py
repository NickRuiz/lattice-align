#!/usr/bin/env python3
# -*- coding: utf8 -*-
"""
This script converts specific morfessor output with srilm tags to moses's
PLF format.
"""

# Author: Tommi A Pirinen <tommi.pirinen@computing.dcu.ie> 2014

#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.

from sys import stdin, stdout, stderr, exit, argv
from math import exp
import argparse
import locale
import csv

def main():
    ap = argparse.ArgumentParser(description=
            "Convert tagged formatted morfessor output into PLF")

    ap.add_argument("--quiet", "-q", action="store_false", dest="verbose",
            default=False,
            help="do not print output to stdout while processing")
    ap.add_argument("--verbose", "-v", action="store_true", default=False,
            help="print each step to stdout while processing")
    ap.add_argument("--version", "-V", action="version")
    ap.add_argument("--input-format-separator", "-I", action="store",
            metavar="ISEP", help="split morphs by ISEP",
            required=True)
    args = ap.parse_args()

    in_s = False
    linen = 0
    edges_at = dict()
    prefixes = dict()
    currentword = ''
    for line in stdin:
        linen += 1
        fields = line.split('\t')
        if len(fields) != 3:
            print("Line", linen, "is not {compound}\\t{analysis}\\t{logprob}\\n:",
                    line)
            exit(1)
        if fields[0] == '<s>':
            print("(", end='')
            in_s = True
        elif fields[0] == '</s>':
            print(")")
            in_s = False
        elif not in_s:
            continue
        elif currentword == fields[0]:
            segs = fields[1].split(args.input_format_separator)
            nsegs = len(segs)
            prefix = ''
            for seg in segs:
                if prefix not in edges_at:
                    edges_at[prefix] = [(seg, (-float(fields[2])) * nsegs)]
                else:
                    edges_at[prefix] += [(seg, (-float(fields[2])) * nsegs)]
                prefix += seg
                prefixes[prefix] = len(prefix)
        elif currentword != fields[0]:
            # print current
            i = 0
            keys = sorted(prefixes.keys(), key=len)
            for key in keys:
                prefixes[key] = i
                i += 1
            keys = sorted(prefixes.keys(), key=len)
            for key in keys:
                if key in edges_at:
                    print("(", end='')
                    for edge in edges_at[key]:
                        print("('", edge[0], "',", edge[1], ",",
                                prefixes[key + edge[0]] - prefixes[key],
                                "),", end='')
                    print("),", end='')
            # move on
            currentword = fields[0]
            prefixes = dict()
            edges_at = dict()
            prefixes[''] = 0
    exit()


if __name__ == "__main__":
    main()

