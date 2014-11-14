#!/bin/bash
for ie in '' '--model1-with-input-epsilons' ; do
    for  zpm in '' '--model1-zero-prob-maxw' ; do
        for otm in '' '--model1-one-to-many' ; do
            for t in 'noalign' 'permutations' 'align' ; do
                echo -- $ie $zpm $otm $t
                python3 dump-src-model1-target-fst.py --permutations-limit 100 --segments europarl.tiny.fin --sentences europarl.tiny.eng --model1 europarl.50k.model1.tsv  $ie $zpm $otm --target=$t -o 50k-$ie-$zpm-$otm-$t
            done
        done
    done
done
