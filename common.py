'''
Created on Sep 13, 2014

@author: Nick Ruiz
'''
import fst

def add_forward_weights(my_fst):
    '''
    Assigns uniform weights to arcs from start to end.
    '''
    for state in my_fst.states:
        arc_count = sum(map(lambda x: 1, state.arcs))
        for arc in state.arcs:
            arc.weight = fst.TropicalWeight(1.0 / arc_count)
#     my_fst.remove_epsilon()
    my_fst.top_sort()
    return my_fst

def add_backward_weights(my_fst):
    '''
    Assigns uniform weights to arcs from end to start.
    '''
    fst_rev = my_fst.reverse()
    fst_rev = add_forward_weights(fst_rev)
    bwd = fst_rev.reverse()
    bwd.remove_epsilon()
    bwd.arc_sort_input()
    bwd.top_sort()
    return bwd

def forward_backward_weights(fsa):
    '''
        Combines and normalizes the forward and backward assigned weights.
        Weights of all arcs in the entire network sum to 1.0.
    ''' 
    fwd = add_forward_weights(fsa)
    bwd = add_backward_weights(fsa)
    
    print(fwd,bwd)
    
    weight_sum = 0.0
    
    for fwd_state in fwd.states:
        bwd_state = bwd[fwd_state.stateid]
        #fwd_arcs = fwd_state.arcs
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
            
    return fwd
    