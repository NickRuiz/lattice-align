
from sys import argv, exit

if len(argv) != 3:
    print("usage", argv[0], "REF TEST")
    exit(1)

total = 0
corrects = 0

try:
    with open(argv[1]) as ref:
        with open(argv[2]) as test:
            for refline in ref:
                testline = next(test)
                refs = set(refline.strip().split())
                tests = set(testline.strip().split())
                corrs = refs & tests
                total += len(refs)
                corrects += len(corrs)
except StopIteration:
    print("Mismatched files...")

print("%d of %d = %f %%" %(corrects, total, 100 * corrects / total))

