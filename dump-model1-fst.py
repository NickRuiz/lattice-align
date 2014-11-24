## This is to dump src sentences, model1 and trg sentences as automata for
## further processing

from __future__ import print_function
from sys import stdout
from math import log, ceil
import argparse
import fst

def dumpfsa(t, outfile):
    for state in t.states:
        if t[state.stateid].final:
            print('{}\t{}'.format(state.stateid, t[state.stateid].final).replace('TropicalWeight(', '')[:-1],
                    file=outfile)
        for arc in state.arcs:
            print('{}\t{}\t{}\t{}\t{}'.format(state.stateid,
                                                 arc.nextstate,
                                                 t.isyms.find(arc.ilabel),
                                                 t.osyms.find(arc.olabel),
                                                 arc.weight).replace('TropicalWeight(', '')[:-1],
                                                 file=outfile)

def model1fsa(model1):
    probs = fst.Transducer()
    for line in model1:
        fields = line.strip().replace('#NULL', '@_EPSILON_SYMBOL_@').split()
        if float(fields[2]) != 0:
            probs.add_arc(0, 0, fields[0], fields[1],-log(float(fields[2])))
    probs[0].final = True
    return probs

def model1fsa_withinputepsilons(model1, maxw):
    probs = fst.Transducer()
    vocab = set()
    for line in model1:
        fields = line.strip().replace('#NULL', '@_EPSILON_SYMBOL_@').split()
        if float(fields[2]) != 0:
            probs.add_arc(0, 0, fields[0], fields[1],-log(float(fields[2])))
        vocab.add(fields[1])
    for v in vocab:
        probs.add_arc(0, 0, '@_EPSILON_SYMBOL_@', v, maxw)
    probs[0].final = True
    return probs

def model1fsa_withzeroprobs(model1, maxw):
    probs = fst.Transducer()
    for line in model1:
        fields = line.strip().replace('#NULL', '@_EPSILON_SYMBOL_@').split()
        if float(fields[2]) != 0:
            probs.add_arc(0, 0, fields[0], fields[1],-log(float(fields[2])))
        else:
            probs.add_arc(0, 0, fields[0], fields[1], maxw)
    probs[0].final = True
    return probs

def model1fsa_onetomany(model1):
    probs = fst.Transducer()
    seenwords = dict()
    higheststate = 0
    for line in model1:
        fields = line.strip().replace('#NULL', '@_EPSILON_SYMBOL_@').split()
        if fields[0] not in seenwords.keys():
            higheststate += 1
            seenwords[fields[0]] = higheststate
            probs.add_arc(higheststate, 0, '@_EPSILON_SYMBOL_@', '@_EPSILON_SYMBOL_@', 0)
        if float(fields[2]) != 0:
            probs.add_arc(0, seenwords[fields[0]],
                          fields[0], fields[1], -log(float(fields[2])))
            probs.add_arc(seenwords[fields[0]], seenwords[fields[0]],
                          fields[0], fields[1], -log(float(fields[2])))
    probs[0].final = True
    return probs


def main():
    ap = argparse.ArgumentParser(description="get 1-best segmentation using alignment data")
    
    ap.add_argument("--verbose", "-v", action="store_true",
            help="Print every step verbosely")
    ap.add_argument("--silent", "--quiet", "-q", action="store_false",
            help="Print every step verbosely")
    ap.add_argument("--model1", "-m", action="store", required=True,
            metavar="M1", help="Load model 1 TSV from M1")
    ap.add_argument("--output", "-o", action="store", required=True,
            metavar="OFILE", help="store output automata in OPFX.*")
    ap.add_argument("--max-weight", "-M", action="store", type=float, 
            default=100000, metavar="MAXW", help="use MAXW as zero prob")
    ap.add_argument("--model1-with-input-epsilons", action="store_true",
            help="add <eps>:x for each word x in target vocabulary to model")
    ap.add_argument("--model1-zero-prob-maxw", action="store_true",
            help="store model1 translations with zero prob as MAXW")
    ap.add_argument("--model1-one-to-many", action="store_true",
            help="allow one to many words translation with product weight")

    args = ap.parse_args()

    src = ''
    trg = ''

    probs = fst.Transducer()
    print('Loading probs from', args.model1)
    with open(args.model1) as model1:
        probs = None
        if args.model1_one_to_many:
            probs = model1fsa_onetomany(model1)
        elif args.model1_with_input_epsilons:
            probs = model1fsa_withinputepsilons(model1, args.max_weight)
        elif args.model1_zero_prob_maxw:
            probs = model1fsa_withzeroprobs(model1, args.max_weight)
        else:
            probs = model1fsa(model1)
        with open(args.output + '.model1.att', 'w') as m1fsa:
            dumpfsa(probs, m1fsa)

if __name__ == '__main__':
    main()


