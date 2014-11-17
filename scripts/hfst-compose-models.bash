#!/bin/bash
if test $# -lt 1 ; then
    echo Usage: $0 OPFX
    exit 1
fi

hfst-compose -v $1.segs.hfst $1.model1.hfst |\
    hfst-compose -v - $1.sents.hfst -o $1.segs2sents.hfst

