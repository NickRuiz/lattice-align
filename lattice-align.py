## This is the CLI file

from __future__ import print_function
import argparse
from ibm import IBM1
from ibmdbm import IBM1dbm

def main():
    ap = argparse.ArgumentParser(description="Convert n-best segments to FST that is actually a lattcie or so")
    ap.add_argument("--segments", "-f", action="store", required=True,
            metavar="FFILE", help="read segments from FFILE")
    ap.add_argument("--sentences", "-e", action="store", required=True,
            metavar="EFILE", help="read sentences from EFILE")
    ap.add_argument("--set-separator", "-s", action="store", default="|",
            metavar="SSEP", help="the set of nbests separated by SSEP")
    ap.add_argument("--morph-separator", "-m", action="store", default=">",
            metavar="MSEP", help="morphs separated by MSEP")
    ap.add_argument("--token-separator", "-t", action="store", default=" ",
            metavar="TSEP", help="between token sets is TSEP")
    ap.add_argument("--compound-separator", "-c", action="store", default="+",
            metavar="CSEP", help="between words of compound is CSEP")
    ap.add_argument("--output-prefix", "-o", action="store", required="True",
            metavar="OPFX", help="save alignments to OPFX.*")
    ap.add_argument("--iterations", "-I", action="store", default="1000",
            type=int, metavar="I", help="iterate at most I times")
    ap.add_argument("--dbm", action="store_true", default=False,
            help="use dbm instead of defaultdict for storing probabilities "
            "(probably more like giza works)")
    ap.add_argument("--verbose", "-v", action="store_true",
            help="Print every step verbosely")
    ap.add_argument("--silent", "--quiet", "-q", action="store_false",
            help="Print every step verbosely")
    args = ap.parse_args()

    src = ''
    trg = ''
    with open(args.segments) as segfile:
        for line in segfile:
            src += (line.replace(args.set_separator, " ").replace(args.morph_separator, " ").replace(args.compound_separator, " "))
    with open(args.sentences) as sentfile:
        for line in sentfile:
            trg += line
    with open(args.output_prefix + ".model1.tsv", "w") as model1:
        if args.dbm:
            t = IBM1dbm(src, trg, args.iterations)
            for key in t.keys():
                print("%s\t%f" %(key, float(t[key])), file=model1)
        else:
            t = IBM1(src, trg, args.iterations)
            for key in sorted(t.keys()):
                print("%s\t%s\t%f" %(key[0], key[1], t[key]), file=model1)

if __name__ == '__main__':
    main()

