#!/bin/bash
for ie in '' '--model1-with-input-epsilons' ; do
    for  zpm in '' '--model1-zero-prob-maxw' ; do
        for otm in '' '--model1-one-to-many' ; do
            echo -- $ie $zpm $otm
            python3 dump-model1-fst.py --model1 example.model1.tsv  $ie $zpm $otm -o 50k-model1-$ie-$zpm-$otm
        done
    done
done
for t in 'noalign' 'permutations' 'align' ; do
    echo -- $t
    python3 dump-src-target-fst.py --segments europarl.100.fin --sentences europarl.100.eng --target=$t -o 50k-data-$t
done
for ie in '' '--model1-with-input-epsilons' ; do
    for  zpm in '' '--model1-zero-prob-maxw' ; do
        for otm in '' '--model1-one-to-many' ; do
            for t in 'noalign' 'permutations' 'align' ; do
                for f in 50k-model1-$ie-$zpm-$otm* ; do
                    ln -vsf $f $(echo $f | sed -e 's/model1-//' -e "s/\./-$t./")
                done
                for f in 50k-data-$t.* ; do
                    ln -vsf $f ${f/data-/$ie-$zpm-$otm-}
                done
            done
        done
    done
done
