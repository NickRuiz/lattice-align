input=$1; shift;

set -x

template=${input%.*}
fstTxt=$template.fst
fstBin=$template.bin.fst
fstDet=$template.bin.det.fst
fstMin=$template.min.fst
isymbols=$template.isyms
osymbols=$template.osyms

# Make the AT&T format
python3 nbest-fst.py $input $fstTxt $isymbols $osymbols

# Binarize
fstcompile --isymbols=$isymbols --osymbols=$osymbols $fstTxt $fstBin

# Determinize
fstdeterminize $fstBin $fstDet

# Minimize
fstminimize $fstDet $fstMin