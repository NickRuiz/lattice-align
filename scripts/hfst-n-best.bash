#!/bin/bash
if test $# -lt 2; then
    echo Usage: $0 OPFX N
    exit 1
fi
hfst-project -p input $1.segs2sents.hfst |\
    hfst-fst2strings -n $2 -X print-space
