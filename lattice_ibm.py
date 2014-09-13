'''
Created on Sep 12, 2014

@author: Nick Ruiz
'''
import fst
import sys, io
from collections import defaultdict, Counter
from lattice import Lattice
import common
from itertools import chain

class LatticeToStringWordAligner(object):
    '''
    Performs word alignment on a collection of lattices
    '''

    def __init__(self, src_lang, tgt_lang, src_syms=None):
        self.src_data = list()
        self.src_vocab = set()
        self.src_lang = src_lang
        self.src_syms = src_syms
        if not self.src_syms:
            self.src_syms = fst.SymbolTable()
        
        self.tgt_data = list()         
        self.tgt_vocab = set()
        self.tgt_lang = tgt_lang
        
        self.probs_tgt_src = dict()
    
    def get_vocab(self, text_list):
        tgt_vocab = Counter(chain(*text_list))
        return set(tgt_vocab.keys())
    
    def load_files(self, dir, src, tgt):
        '''
        TODO: Load a bunch of pre-processed files in a directory.        
        '''
        pass

    def add_bitext(self, src, tgt):
        '''
        Adds a training bitext.
        Input:
        src_data: filepath containing n-best list of src_data hypotheses
        tgt_data: string containing translation
        
        Postcondition:
        A source word lattice is constructed from src_data, compiled into a weighted FSA.
        A bitext containing the weighted source FSA and string tgt_data is stored.
        '''
        src_lattice = Lattice(syms=self.src_syms)
        src_lattice.load_delimited(src)
        # Weight the edges
        src_lattice.forward_backward_weights()
        # Add the NULL token at the front
        src_lattice.prepend_epsilon()
        
        self.src_data.append(src_lattice.fsa)
        # TODO: Figure out how to extract vocabulary from FSA (src_lattice.sigma)
        for arc in common.arcs(src_lattice.fsa):
            self.src_vocab.add(arc.ilabel)
        
        self.tgt_data.append(tgt)
        self.tgt_vocab = self.tgt_vocab.union(set(tgt.split()))
        
    def dump_bitexts(self, out_dir):
        for i in range(len(self.src_data)):
            # Write src fsts
            self.src_data[i].write("%s/%d.%s.fst" % (out_dir, i, self.src_lang))
            with open("%s/%d.%s.txt" % (out_dir, i, self.tgt_lang), 'w') as f:
                f.write("%s\n" % self.tgt_data[i])
                
    def IBM1(self, src, tgt):
        '''
        IBM Model 1: t(tgt|src)
        '''
        # src is already segmented (as fsa/lattice)
        # NULL (epsilon) already prepended to src
        tgt = [i.split() for i in tgt]
        
        print(self.src_vocab)
        print(self.tgt_vocab)
        
        num_probs = len(self.src_vocab) * len(self.tgt_vocab)
        default_prob = 1.0 / len(self.tgt_vocab)
        t = defaultdict(lambda: default_prob)
        
        convergent_threshold=1e-2
        globally_converged = False
        iteration_count = 0
        
        while not globally_converged:
            count = defaultdict(float) # count(e|f)
            total = defaultdict(float) # total(f)
            
            for src_fsa, tgt_str in zip(src, tgt):
                s_total = {}            # Walk through each arc
                for arc in common.arcs(src_fsa):
                    s_total[arc.ilabel] = 0.0
                    for tgt_word in tgt_str:
                        s_total[arc.ilabel] += t[arc.ilabel, tgt_word] * float(arc.weight)
                        
                for arc in common.arcs(src_fsa):
                    for tgt_word in tgt_str:
                        # Normalize probabilities
                        if s_total[arc.ilabel] == 0:
                            # print (arc.ilabel, tgt_word, 'uh-oh')
                            # TODO: Epsilons (NULLs) aren't working
                            continue
                        
                        cnt = t[arc.ilabel, tgt_word] / s_total[arc.ilabel]
                        # Summing the prob of each src word given tgt_word
                        count[arc.ilabel, tgt_word] += cnt
                        total[tgt_word] += cnt
                        
            num_converged = 0
            for tgt_word in self.tgt_vocab:
                for src_word in self.src_vocab:
                    new_prob = count[src_word, tgt_word] / total[tgt_word]
                    delta = abs(t[src_word, tgt_word] - new_prob)
                    if delta < convergent_threshold:
                        num_converged += 1
                    t[src_word, tgt_word] = new_prob
                    
                iteration_count += 1
                if num_converged == num_probs:
                    globally_converged = True
            
        return t
            
            
            
            
            
            
        