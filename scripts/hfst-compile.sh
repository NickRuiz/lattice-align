#!/bin/bash
if test $# -lt 1 ; then
    echo Usage: $0 OPFX
    exit 1
fi

hfst-txt2fst -v $1.model1.att -o $1.model1.hfst
hfst-txt2fst -v $1.segs.att -o $1.segs.hfst
hfst-txt2fst -v $1.sents.att -o $1.sents.hfst
