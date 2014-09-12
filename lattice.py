'''
Created on Sep 11, 2014

@author: Nick Ruiz
'''
import sys, io
import fst
import re, math

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
        
        with open(nbest_file, 'r') as f_in:
            for line in f_in:
                line = line.strip()
                
                b = fst.linear_chain(line.split(), self.sigma)
                a = a.union(b)
                
        a.remove_epsilon()
        d = a.determinize()
        d.minimize()
        
        self.fsa = d
        
    def load_delimited(self, str, delim='|', seg_chars='>+'):
        '''
        Loads a sentence with segmentation like the example below.
        TODO: Refactor this function; it's inefficient
        TODO: Multiple arcs for same segmentation split for a word. See example.
              For now, it's addressed by determinizing the FSA.
        Finnish example:
        Istuntokauden|istunto+kaude>n uudelleenavaaminen|uudelleen+avaaminen .|.
        '''
        
        a = fst.Acceptor()
        re_seg_delim = re.compile('[%s]' % seg_chars)
        
        state_idx = 0
        prev_states = [0]
        
        # split words
        words = str.strip().split(' ')
        for word in words:
            new_states = []
            # split on forms
            forms = word.split(delim)
            tokens = []
            
            for form in forms:
                # split on segments
                segs = re_seg_delim.split(form)
#                 print(word, form, segs)               
                tokens.append((len(segs), segs))
                
            # Add topological ordering
            tokens.sort(reverse=True)
            max_length = len(tokens[0])
            
            for j in range(len(tokens)):
                toks = tokens[j]
                for i in range(len(toks[1])):
                    tok = toks[1][i]
                    # Add an arc
                    state_idx += 1
                    for istate in prev_states:
                        prev_istate = state_idx - 1
                        if i == 0:
                            # Use istate for the first tok in the sequence
                            prev_istate = istate
                        
                        # TODO: INEFFICIENT; REFACTOR.
                        if i == len(toks[1]) - 1:
                            if j == 0:
                                # Record the last state index
                                a.add_arc(prev_istate, state_idx, tok)
                            else:
                                # Connect to the existing state
                                a.add_arc(prev_istate, new_states[0], tok)
                                state_idx -= 1
                        else:
                            a.add_arc(prev_istate, state_idx, tok)
                        
                    if j == 0 and i == len(toks[1])-1:
                        new_states.append(state_idx)
            prev_states = new_states
        
        # Add inal states
        for state in new_states:
            a[state].final = True
            
        # Removes duplicate arcs; TODO: don't rely on this.
#         return a.determinize()
        self.fsa = a.determinize()
        
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
#                 print(scaled_weight, prob_total)
        assert(abs(1.0 - prob_total) < 0.00001)
                
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
        