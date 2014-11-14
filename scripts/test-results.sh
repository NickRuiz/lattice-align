#!/bin/bash
for ie in '' '--model1-with-input-epsilons' ; do
    for  zpm in '' '--model1-zero-prob-maxw' ; do
        for otm in '' '--model1-one-to-many' ; do
            for t in 'noalign' 'permutations' 'align' ; do
                echo -- $ie $zpm $otm $t
                bash scripts/hfst-compile.sh 50k-$ie-$zpm-$otm-$t
                bash scripts/hfst-compose-models.bash 50k-$ie-$zpm-$otm-$t
                bash scripts/hfst-n-best.bash 50k-$ie-$zpm-$otm-$t 1 > results-50k-$ie-$zpm-$otm-$t
            done
        done
    done
done

