'''
Created on Sep 11, 2014

@author: Nick Ruiz
'''
import sys, io
import fst

def linear_chain_tok(text, syms=None, semiring='tropical', str=" "):
    """linear_chain(text, syms=None) -> linear chain acceptor for the given input text"""
    chain = fst.Acceptor(syms, semiring=semiring)
    for i, c in text.split(str):
        chain.add_arc(i, i+1, c)
    chain[i+1].final = True
    return chain

class Lattice(object):
    '''
    classdocs
    '''
    
    fsa = fst.Acceptor()
    
    def __init__(self):
        '''
        Constructor
        '''
        self.fsa = fst.Acceptor()
        self.sigma = fst.SymbolTable()
        
    def load_nbest(self, nbest_file):
        """
        cat >text.fst <<EOF
        0 1 a x .5
        0 1 b y 1.5
        1 2 c z 2.5
        2 3.5
        EOF
        """
        a = fst.Acceptor()
        sigma = fst.SymbolTable()
        
        with open(nbest_file, 'r') as f_in:
            for line in f_in:
                line = line.strip()
                
                b = fst.linear_chain(line.split(), sigma)
                a = a.union(b)
                
        a.remove_epsilon()
        d = a.determinize()
        d.minimize()
        
        self.fsa = d
        self.sigma = sigma
        
    def load_nbest_iter(self, nbest_file):
        """
        cat >text.fst <<EOF
        0 1 a x .5
        0 1 b y 1.5
        1 2 c z 2.5
        2 3.5
        EOF
        """
        a = fst.Acceptor()
        sigma = fst.SymbolTable()
        
        with open(nbest_file, 'r') as f_in:
            for line in f_in:
                line = line.strip()
                
                b = fst.linear_chain(line.split(), sigma)
                a = a.union(b)
                
                a.remove_epsilon()
                a = a.determinize()
                a.minimize()
        
        self.fsa = a
        self.sigma = sigma
        
    def add_forward_weights(self, my_fst):
        for state in my_fst.states:
            arc_count = sum(map(lambda x: 1, state.arcs))
            for arc in state.arcs:
                arc.weight = fst.TropicalWeight(1.0 / arc_count)
        return my_fst
    
    def add_backward_weights(self, my_fst):
        fst_rev = my_fst.reverse()
        fst_rev = self.add_forward_weights(fst_rev)
        bwd = fst_rev.reverse()
        bwd.remove_epsilon()
        bwd.arc_sort_input()
        return bwd
    
    def forward_backward_weights(self):
        fwd = self.add_forward_weights(self.fsa)
        bwd = self.add_backward_weights(self.fsa)
        
        weight_sum = 0.0
        
        for fwd_state in fwd.states:
            bwd_state = bwd[fwd_state.stateid]
            fwd_arcs = fwd_state.arcs
            bwd_arcs = bwd_state.arcs
            for fwd_arc in fwd_state.arcs:
                bwd_arc = bwd_arcs.next()
                assert(fwd_arc.ilabel == bwd_arc.ilabel and fwd_arc.olabel == bwd_arc.olabel)
                joint_weight = float(fwd_arc.weight) * float(bwd_arc.weight)
                fwd_arc.weight = fst.TropicalWeight(joint_weight)
                weight_sum += joint_weight
                
        prob_total = 0.0
        for state in fwd.states:
            for arc in state.arcs:
                scaled_weight = float(arc.weight) / weight_sum
                arc.weight = fst.TropicalWeight(scaled_weight)
                prob_total += scaled_weight
        assert(prob_total == 1.0)
                
        self.fsa = fwd
        
    
    def prepend_epsilon(self):
        a = fst.Acceptor()
        a[0].final = True
        self.fsa = a + self.fsa
            
    def write_fst(self, path):
        self.fsa.write(path)
        
if __name__ == "__main__":
    l = Lattice()
    l.load_nbest(sys.argv[1])
    l.write_fst(sys.argv[2])
        