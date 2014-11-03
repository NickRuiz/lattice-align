## This is to dump src sentences, model1 and trg sentences as automata for
## further processing

from math import log
import argparse
import fst

def dumpfsa(t, outfile):
    for state in t.states:
        if t[state.stateid].final:
            print(state.stateid, file=outfile)
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

def permutations_r(fsa, seen, tokens, index, next_available):
    left = set(tokens) - seen
    if len(left) == 0:
        fsa[index].final = True
    for token in left:
        fsa.add_arc(index, next_available, token)
        old_seen = seen
        seen.add(token)
        old_index = next_available
        next_available += 1
        next_available = permutations_r(fsa, seen, tokens, old_index, next_available)
        seen.remove(token)
    return next_available

def sent2fsa_permutations(line, symtab):
    tokens = line.strip().split()
    fsa = fst.Acceptor(symtab)
    next_available = 1
    for token in tokens:
        fsa.add_arc(0, next_available, token)
        seen = set([token])
        old_index = next_available
        next_available += 1
        next_available = permutations_r(fsa, seen, tokens, old_index, next_available)
    return fsa

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
            default=100.1, metavar="MAXW", help="use MAXW as zero prob")
    ap.add_argument("--model1-with-input-epsilons", action="store_true",
            help="add <eps>:x for each word x in target vocabulary to model")
    ap.add_argument("--model1-zero-prob-maxw", action="store_true",
            help="store model1 translations with zero prob as MAXW")
    ap.add_argument("--target", action="store", default="noalign",
            metavar="ALIGN", help="Use ALIGN as target automaton structure")
    args = ap.parse_args()

    src = ''
    trg = ''

    probs = fst.Transducer()
    print('Loading probs')
    vocab = set()
    with open(args.model1) as model1:
        for line in model1:
            fields = line.strip().replace('#NULL', '@_EPSILON_SYMBOL_@').split()
            if float(fields[2]) != 0:
                probs.add_arc(0, 0, fields[0], fields[1],-log(float(fields[2])))
            elif args.model1_zero_prob_maxw:
                # XXX: this should be backoff stuff, right?
                probs.add_arc(0, 0, fields[0], fields[1], args.max_weight)
            else:
                # 1 is sink state cause nonfinal
                probs.add_arc(0, 1, fields[0], fields[1])
            vocab.add(fields[1])
        if args.model1_with_input_epsilons:
            for v in vocab:
                probs.add_arc(0, 0, '@_EPSILON_SYMBOL_@', v, args.max_weight)
        probs[0].final = True
        with open(args.output + '.model1.att', 'w') as m1fsa:
            dumpfsa(probs, m1fsa)
    output = open(args.output, 'w')
    print('processing data')
    linen = 0
    segfsafile = open(args.output + ".segs.att", 'w')
    sentfsafile = open(args.output + ".sents.att", "w")
    with open(args.segments) as segfile:
        with open(args.sentences) as sentfile:
            for segs in segfile:
                sent = next(sentfile)
                segfsa = segmentation2fsa(segs, probs.isyms)
                sentfas = None
                if args.target == "noalign":
                    sentfsa = sent2fsa_noalign(sent, probs.osyms)
                elif args.target == "permutations":
                    sentfsa = sent2fsa_permutations(sent, probs.osyms)
                else:
                    sentfsa = sent2fsa(sent, probs.osyms)
                dumpfsa(sentfsa, sentfsafile)
                dumpfsa(segfsa, segfsafile)
                # In HFST the fst archive format is -- separated
                # I don't know how to encode this for openfst's FAR
                # archives...
                print("--", file=sentfsafile)
                print("--", file=segfsafile)

if __name__ == '__main__':
    main()


