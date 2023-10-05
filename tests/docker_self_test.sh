#!/bin/bash

# argument: homework number
# this runs in /usr/src in the container, and assumes that user .py files are mounted in /tmp
# it also assumes grading_script_hwX.sh and clean_output.sh are in /usr/src
# it writes the diff file back to the mounted directory /tmp

cd /usr/src
cp /tmp/*.py .
./grading_script_hw$1.sh
for outputfile in `ls hw$1_*.out`
do
  ./clean_output.sh $outputfile
  ./clean_output.sh correct_$outputfile
  echo "##########################################" >> diffs_hw$1.txt
  echo $outputfile >> diffs_hw$1.txt
  echo "##########################################" >> diffs_hw$1.txt
  diff $outputfile correct_$outputfile >> diffs_hw$1.txt
done
cp diffs_hw$1.txt /tmp
