#!/bin/bash

ERROR=/dev/stderr
input=/dev/stdin
output=/dev/stdout

function usage()
{
  echo "\
Usage: $(basename $0) type src trg [input [output]]
Mandatory parameters
  type         one of src, ref, tst
  src          source language code
  trg          target language code
Optional parameters
  input        plain text to wrap
  output       wrapped text" > "$ERROR"
}

if [ $# -lt 3 -o $# -gt 5 ]
then
  usage
  exit 2
fi

type="$1"
src="$2"
trg="$3"

if [ $# -ge 4 ]; then input="$4"; fi
if [ ! -e "$input" ]
then
  echo "Error: file '$input' does not exist."
  exit 1
fi

if [ $# -eq 5 ]; then output="$5"; fi

cat "$input" | \

gawk -v type="$type" -v src="$src" -v trg="$trg" '
BEGIN{
  if (type == "src")
  {
    print "<srcset setid=\"fake-id\" srclang=\"" src "\">"
    print "<doc docid=\"fake-doc\" genre=\"fake-genre\" origlang=\"fake-lang\">"
  }
  else if (type == "ref")
  {
    print "<refset trglang=\"" trg "\" setid=\"fake-id\" srclang=\"" src "\">"
    print "<doc sysid=\"ref\" docid=\"fake-doc\" genre=\"fake-genre\" origlang=\"fake-lang\">"
  }
  else if (type == "tst")
  {
    print "<tstset trglang=\"" trg "\" setid=\"fake-id\" srclang=\"" src "\">"
    print "<DOC sysid=\"fake-system\" docid=\"fake-doc\" genre=\"fake-genre\" origlang=\"fake-lang\">"
  }
}
{
  print "<seg id=\"" NR "\">" $0 "</seg>"
}
END{
  print "</doc>"
  if (type == "src")
  {
    print "</srcset>"
  }
  else if (type == "ref")
  {
    print "</refset>"
  }
  else if (type == "tst")
  {
    print "</tstset>"
  }
}
' > "$output"

exit 0
