'''
Created on Sep 12, 2014

@author: Nick Ruiz
'''
import fst
import sys, io
from collections import defaultdict, Counter
from lattice import Lattice
from itertools import chain

class LatticeToStringWordAligner(object):
    '''
    Performs word alignment on a collection of lattices
    '''

    def __init__(self, src_lang, tgt_lang):
        self.src_data = list()
        self.src_vocab = set()
        self.src_lang = src_lang
        
        self.tgt_data = list()         
        self.tgt_vocab = set()
        self.tgt_lang = tgt_lang
    
    def get_vocab(self, text_list):
        tgt_vocab = Counter(chain(*text_list))
        return set(tgt_vocab.keys())

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
        src_lattice = Lattice()
        src_lattice.load_delimited(src)
        src_lattice.forward_backward_weights()
        self.src_data.append(src_lattice.fsa)
        # TODO: Figure out how to extract vocabulary from FSA (src_lattice.sigma)
        
        self.tgt_data.append(tgt)
        self.tgt_vocab = self.get_vocab(tgt)
        
    def dump_bitexts(self, out_dir):
        for i in range(len(self.src_data)):
            # Write src fsts
            self.src_data[i].write("%s/%d.%s.fst" % (out_dir, i, self.src_lang))
            with open("%s/%d.%s.txt" % (out_dir, i, self.tgt_lang), 'w') as f:
                f.write("%s\n" % self.tgt_data[i])
                
    def init_probs(self):
        pass
        