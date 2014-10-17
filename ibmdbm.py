from collections import defaultdict, Counter
from itertools import chain
import argparse
try:
    import dbm
except ImportError:
    import anydbm as dbm

def IBM1dbm(src, trg, iterations):
    # Adds the `#NULL` token to the target sentence.
    # Convert into docstream.
    src = [i.split() for i in  src.split('\n')]
    trg = [list(["#NULL"]+ i.split()) for i in trg.split('\n')]
    src_vocab = Counter(chain(*src))
    trg_vocab = Counter(chain(*trg))
    num_probs = len(src_vocab) * len(trg_vocab)
    default_prob = 1.0 / len(src_vocab)
    t = dbm.open('tef', 'n')
    # cooccurrence set, so in the maximisation step we check only word pairs that cooccur
    cooccur = set()
    for srcline, trgline in zip(src, trg):
        for srcword in srcline:
              for trgword in trgline:
                    cooccur.add( (srcword,trgword) )
    convergent_threshold=1e-7
    globally_converged = False
    probabilities = []
    iteration_count = 0
    while not globally_converged and iteration_count < iterations:
        iteration_count += 1
        print("Iteration %d of %d" %(iteration_count, iterations))
        count = dbm.open('count', 'n') # count(e|f)
        total = defaultdict(float) # total(f)
        for srcline, trgline in zip(src, trg):
            s_total = {} # Sum of probabilities for this sentence pair.
            for srcword in srcline:
                s_total[srcword] = 0.0
                for trgword in trgline:
                    key = srcword + '\t' + trgword
                    if not key in t:
                        t[key] = str(default_prob)
                    s_total[srcword] += float(t[key])
            for srcword in srcline:
                for trgword in trgline:
                    key = srcword + '\t' + trgword
                    # Normalize probabilities.
                    cnt = float(t[key]) / float(s_total[srcword])
                    # Summing the prob of srcword given trgword.
                    if not key in count:
                        count[key] = '0.0'
                    tmp = float(count[key])
                    tmp += cnt
                    count[key] = str(tmp)
                    total[trgword] += cnt
        num_converged = 0
        for (srcword, trgword) in cooccur:
            key = srcword + '\t' + trgword
            new_prob = float(count[key]) / total[trgword]
            delta = abs(float(t[key]) - new_prob)
            if delta < convergent_threshold:
                num_converged += 1
            t[key] = str(new_prob)
        if num_converged >= len(cooccur):
            globally_converged = True
    return t

def IBM2(src, trg, num_iter=1000, smoothing=True):
    # Carry over t(e|f) from Model 1.s
    t_ef = IBM1(src, trg)
    
    # Convert into docstream.
    src = [i.split() for i in src.split('\n')]
    trg = [list(["#NULL"]+ i.split()) for i in trg.split('\n')]
    src_vocab = Counter(chain(*src))
    trg_vocab = Counter(chain(*trg))
    
    # Initialize a(i|j, l_e, l_f) = 1/(l_f + 1) for all i, j, l_e, l_f
    default_prob = 1.0 / len(trg_vocab)
    align = defaultdict(lambda: 
                    defaultdict(lambda: 
                            defaultdict(lambda: 
                                    defaultdict(lambda: default_prob))))
    # while not coverage do
    for i in range(num_iter):
        # Initialize count(e|f) = 0 for all e,f
        count_ef = defaultdict(float)
        # Initialize total(f) = 0 for all f
        total_f = defaultdict(float)
        # Initializa count_a(i|j, l_e, l_f) = 0 for all i, j, l_e, l_f
        count_align = defaultdict(lambda: 
                                defaultdict(lambda: 
                                        defaultdict(lambda: 
                                                defaultdict(lambda: 0.0))))
        # Initialize total_a(j, l_e, l_f) =0 for all j, l_e, l_f 
        total_align = defaultdict(lambda: 
                                defaultdict(lambda: 
                                        defaultdict(lambda: 0.0)))
        # Initialize s_total
        s_total = defaultdict(float)
        
        # for all sentence_pairs (e,f) do
        for src_sent, trg_sent in zip(src, trg):
            # l_e = length(e) , l_f = length(f)
            l_e = len(src_sent)
            l_f = len(trg_sent)
            # Compute normalization.
            for j in range(l_e): # for j = 1 ... l_e do
                e_j = src_sent[j]
                s_total[e_j] = 0 # s-total(e_j) = 0
                for i in range(l_f): # for i = 0 .. l f do
                    f_i = trg_sent[i]
                    # s-total(e_j) += t(e_j | f_i) * a(i | j, l_e, l_f)
                    _prob = t_ef[e_j,f_i] * align[i][j][l_e][l_f]
                    s_total[e_j] += _prob
            # Collect counts.
            for j in range(l_e): # for j = 1 ... l_e do
                e_j = src_sent[j]
                for i in range(l_f): # for i = 0 .. l f do
                    f_i = trg_sent[i]
                    # c = t(e_j | f_i) * a(i | j, l_e, l_f) / s-total(e_j)
                    c = t_ef[e_j,f_i] * align[i][j][l_e][l_f] / s_total[e_j]
                    # count(e_j | f_i) += c
                    count_ef[e_j, f_i] += c
                    # total(f_i) += c
                    total_f[f_i] += c
                    # count_a(i|j, l_e, l_f) += c
                    count_align[i][j][l_e][l_f] += c
                    # total_a(j, l_e, l_f) += c
                    total_align[j][l_e][l_f] += c
                    
        # Estimate probabilities.
        # Reinitialize t(e|f) = 0 for all e,f
        t = defaultdict(lambda: default_prob) 
        # Reinitialize a(i | j, l_e, l_f) = 0 for all i, j, l_e, lf
        align = defaultdict(lambda: 
                        defaultdict(lambda: 
                                defaultdict(lambda: 
                                        defaultdict(lambda: default_prob))))
        if smoothing:        
            # Smooth the counts for alignments
            for src_sent, trg_sent in zip(src, trg):
                # l_e = length(e) , l_f = length(f)
                l_e = len(src_sent)
                l_f = len(trg_sent)
                
                # Find minimal probability
                laplace = 1.0
                for i in range(l_e):
                    for j in range(l_f):
                        value = count_align[i][j][l_e][l_f]
                        if 0 < value < laplace:
                            laplace = value
                            
                laplace *= 0.5
                for i in range(l_f):
                    for j in range(l_e):
                        count_align[i][j][l_e][l_f] += laplace
                        
                initial_value = laplace * l_e
                for j in range(l_e):
                    total_align[j][l_e][l_f] += initial_value
            # Estimate the new lexical translation probabilities
            for e,f in t:
                t[e,f]  = count_ef[e,f] / total_f[f]  
        
        # for all e,f do
        for e in src_vocab:
            for f in trg_vocab:
                # t(e|f) = count(e|f) / total(f)
                t[e,f] = count_ef[e,f] / total_f[f]
        
        
        # for all i, j, l_e, l_f do
        for src_sent, trg_sent in zip(src, trg):
            # l_e = length(e) , l_f = length(f)
            l_e = len(src_sent)
            l_f = len(trg_sent)
            # for all i, j, l_e, l_f do
            for i in range(l_e):
                for j in range(l_f):
                    try:
                        # a(i | j, l_e, l_f) = count_a(i | j, l_e, l_f) / total_a(j, l_e, l_f)
                        _prob = count_align[i][j][l_e][l_f] / total_align[j][l_e][l_f]
                    except:
                        _prob = 0.0
                    align[i][j][l_e][l_f] = _prob

    return t_ef, align

