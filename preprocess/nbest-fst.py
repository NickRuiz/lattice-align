'''
Created on Sep 10, 2014

@author: Nick
'''
import sys

def main(args):
    """
    cat >text.fst <<EOF
    0 1 a x .5
    0 1 b y 1.5
    1 2 c z 2.5
    2 3.5
    EOF
    """
    nbest_file = sys.argv[1]
    fst_file = sys.argv[2]
    isyms_file = sys.argv[3]
    osyms_file = sys.argv[4]
    
    idx_count = 0
    label_count = 0
    label_map = dict()
    
    with open(nbest_file, 'r') as f_in:
        with open(fst_file, 'w') as fst_out: 
            with open(isyms_file, 'w') as isyms_out:
                with open(osyms_file, 'w') as osyms_out:
                    isyms_out.write("<eps> 0\n")
                    for line in f_in:
                        line = line.strip()
                        prev_idx = 0
                        for tok in line.split():
                            curr_idx = prev_idx + 1
                            if prev_idx == 0:
                                curr_idx = idx_count + 1
                            fst_out.write("%d %d %s %s\n" % (prev_idx, curr_idx, tok, tok))
                            prev_idx = curr_idx
                            
                            if tok not in label_map.keys():
                                label_count += 1
                                label_map[tok] = label_count
                                isyms_out.write("%s %d\n" % (tok, label_map[tok]))
                                osyms_out.write("%s %d\n" % (tok, label_map[tok]))
                        idx_count = prev_idx
                        
if __name__ == '__main__':
    main(sys.argv[1:])
    
                