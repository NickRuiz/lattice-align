## This is to dump src sentences, model1 and trg sentences as automata for
## further processing

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

def segmentation2fsa(line, symtab):
    tokens = line.split(' ')
    fsa = fst.Acceptor(symtab)
    for token_index in range(len(tokens)):
        segmentations = tokens[token_index].strip().split('|')
        word_start = 1000 * token_index
        word_end = (token_index + 1) * 1000
        for segment_index in range(len(segmentations)):
            segment_start = word_start + 100 * segment_index
            segs = segmentations[segment_index].replace('+', '>').split('>')
            for i in range(len(segs)):
                if segs[i] == '':
                    continue
                if i == len(segs) - 1:
                    fsa.add_arc(segment_start + i, word_end, segs[i])
                elif i == 0:
                    fsa.add_arc(word_start, segment_start + i + 1, segs[i])
                else:
                    fsa.add_arc(segment_start + i, segment_start + i + 1, segs[i])
    fsa[len(tokens)*1000].final = True
    return fsa

def segmentation2list(line):
    '''turn ambiguous segmentation to list of possible segmentation paths'''
    tokens = line.split(' ')
    linears = ['']
    for token in tokens:
        segmentations = token.split('|')
        path_count = len(linears)
        # the number of new paths is ambiguity*
        linears = linears * len(segmentations)
        for segment_index in range(len(segmentations)):
            # add new segments to each of paths
            for i in range(path_count):
                linears[i + segment_index * path_count] +=  ' ' + segmentations[segment_index].replace('>', ' ').replace('+', ' ')
    return [x.strip() for x in linears]

def permutations_r(fsa, seen, tokens, index, next_available, omission_penalty, base_penalty):
    left = set(tokens) - seen
    if len(left) == 0:
        fsa[index].final = base_penalty
    else:
        fsa[index].final = base_penalty + omission_penalty * len(left)
    for token in left:
        fsa.add_arc(index, next_available, token)
        old_seen = seen
        seen.add(token)
        old_index = next_available
        next_available += 1
        next_available = permutations_r(fsa, seen, tokens, old_index, next_available, omission_penalty, base_penalty)
        seen.remove(token)
    return next_available


def ngram2fsa_permutations(tokens, symtab, maxw, unused):
    fsa = fst.Acceptor(symtab)
    next_available = 1
    for token in tokens:
        fsa.add_arc(0, next_available, token)
        seen = set([token])
        old_index = next_available
        next_available += 1
        next_available = permutations_r(fsa, seen, tokens, old_index, next_available, maxw, unused)
    return fsa

def sent2fsa_permutations(line, symtab, maxw, n):
    tokens = line.strip().split()
    ntokens = len(line.strip().split())
    if n >= ntokens:
        return ngram2fsa_permutations(tokens, symtab, maxw, 0)
    fsa = fst.Acceptor(symtab)
    #fsa[0].final = maxw * ntokens + 1
    for start in range(n):
        splits = [x * n + start for x in range(int(ceil(float(ntokens) / n)))]
        fsa_segments = fst.Acceptor(symtab)
        fsa_segments[0].final = maxw * (n - start)
        for i in range(len(splits)):
            if (i == 0 and splits[i] == 0) or (i == len(splits) and splits[i] == ntokens):
                continue
            elif i == 0:
                ngram_permutations = ngram2fsa_permutations(tokens[:splits[i]], symtab, maxw, (ntokens - splits[i]) * maxw)
            elif i == len(splits):
                ngram_permutations = ngram2fsa_permutations(tokens[splits[i-1]:], symtab, maxw, 0)
            else:
                ngram_permutations = ngram2fsa_permutations(tokens[splits[i-1]:splits[i]], symtab, maxw, (ntokens - splits[i]) * maxw)
            fsa_segments.concatenate(ngram_permutations)
        fsa = fsa.union(fsa_segments)
    return fsa

import itertools

def permutation_lists(line, n):
    tokens = line.strip().split()
    ntokens = len(line.strip().split())
    if n >= ntokens:
        return list(itertools.permutations(tokens))
    all_perms = []
    for start in range(n):
        splits = [x * n + start for x in range(int(ceil(float(ntokens) / n)))]
        ngrams = []
        for i in range(len(splits) + 1 ):
            if i == 0 and splits[i] == 0:
                continue
            elif i == 0:
                ngram_perms = itertools.permutations(tokens[:splits[i]])
            elif i == len(splits):
                ngram_perms = itertools.permutations(tokens[splits[i-1]:])
            else:
                ngram_perms = itertools.permutations(tokens[splits[i-1]:splits[i]])
            ngrams = ngrams + [list(ngram_perms)]
        all_perms += [ngrams]


def sent2fsa_noalign(line, symtab):
    tokens = line.strip().split()
    fsa = fst.Acceptor(symtab)
    for token_index in range(len(tokens)):
        fsa.add_arc(0, 0, tokens[token_index])
    fsa[0].final = True
    return fsa

def sent2fsa(line, symtab):
    tokens = line.strip().split()
    fsa = fst.Acceptor(symtab)
    for token_index in range(len(tokens)):
        fsa.add_arc(token_index, token_index + 1, tokens[token_index])
    fsa[len(tokens)].final = True
    return fsa

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
    seenwords = set()
    currentstate = 0
    for line in model1:
        fields = line.strip().replace('#NULL', '@_EPSILON_SYMBOL_@').split()
        if fields[0] not in seenwords:
            currentstate += 1
            probs.add_arc(0, currentstate, fields[0], '@_EPSILON_SYMBOL_@', 0)
            probs.add_arc(currentstate, 0, '@_EPSILON_SYMBOL_@', '@_EPSILON_SYMBOL_@', 0)
            seenwords.add(fields[0])
        if float(fields[2]) != 0:
            probs.add_arc(currentstate, currentstate, '@_EPSILON_SYMBOL_@', fields[1],-log(float(fields[2])))
    probs[0].final = True
    return probs


def main():
    ap = argparse.ArgumentParser(description="get 1-best segmentation using alignment data")
    
    ap.add_argument("--verbose", "-v", action="store_true",
            help="Print every step verbosely")
    ap.add_argument("--silent", "--quiet", "-q", action="store_false",
            help="Print every step verbosely")
    ap.add_argument("--segments", action="store", required=True,
            metavar="SEGFILE", help="Load segmentations from SEGFILE")
    ap.add_argument("--sentences", action="store", required=True,
            metavar="SENTFILE", help="Load sentences from SENTFILE")
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
    ap.add_argument("--target", action="store", default="noalign",
            metavar="ALIGN", help="Use ALIGN as target automaton structure")
    ap.add_argument("--permutations-limit", action="store", default=5,
            metavar="PMAX", help="move at most PMAX tokens when considering permutations")

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
    output = open(args.output, 'w')
    print('processing data in ', args.segments, 'and', args.sentences)
    linen = 0
    segfsafile = open(args.output + ".segs.att", 'w')
    sentfsafile = open(args.output + ".sents.att", "w")
    with open(args.segments) as segfile:
        with open(args.sentences) as sentfile:
            linen = 0
            for segs in segfile:
                sent = next(sentfile)
                linen += 1
                print(linen, '...')
                segfsa = segmentation2fsa(segs, probs.isyms)
                sentfas = None
                if args.target == "noalign":
                    sentfsa = sent2fsa_noalign(sent, probs.osyms)
                elif args.target == "permutations":
                    permutation_lists(sent, int(args.permutations_limit))
                    continue
                    #sentfsa = sent2fsa_permutations(sent, probs.osyms, args.max_weight, int(args.permutations_limit))
                elif args.target == 'align':
                    sentfsa = sent2fsa(sent, probs.osyms)
                else:
                    print("invalid --target", args.target)
                    exit(1)
                dumpfsa(sentfsa, sentfsafile)
                dumpfsa(segfsa, segfsafile)
                # In HFST the fst archive format is -- separated
                # I don't know how to encode this for openfst's FAR
                # archives...
                print("--", file=sentfsafile)
                print("--", file=segfsafile)

if __name__ == '__main__':
    main()


