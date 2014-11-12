#!/bin/bash
if test $# -lt 1 ; then
    echo Usage: $0 OPFX
    exit 1
fi

hfst-head -v -n 1 $1.segs.hfst |\
    hfst-minimize -v |\
    hfst-fst2txt -v -f dot -o $1.segs.dot
hfst-fst2txt -v -f dot $1.model1.hfst -o $1.model1.dot
hfst-head -v -n 1 $1.segs.hfst |\
    hfst-compose -v - $1.model1.hfst |\
    hfst-minimize -v |\
    hfst-fst2txt -v -f dot -o $1.segs2model1.dot
hfst-head -v -n 1 $1.sents.hfst |\
    hfst-compose -v $1.model1.hfst - |\
    hfst-minimize -v |\
    hfst-fst2txt -v -f dot -o $1.model1sents.dot
hfst-head -v -n 1 $1.sents.hfst |\
    hfst-fst2txt -v -f dot -o $1.sents.dot
hfst-head -v $1.segs2sents.hfst -n 1 |\
    hfst-minimize |\
    hfst-fst2txt -v -f dot -o $1.segs2sents.dot

dot -Tpdf $1.segs.dot -o$1.segs.pdf
dot -Tpdf $1.sents.dot -o$1.sents.pdf
dot -Tpdf $1.model1.dot -o$1.model1.pdf
dot -Tpdf $1.segs2model1.dot -o$1.segs2model1.pdf
dot -Tpdf $1.model1sents.dot -o$1.model1sents.pdf
dot -Tpdf $1.segs2sents.dot -o$1.segs2sents.pdf

