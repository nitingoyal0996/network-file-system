#!/bin/sh

# This is to generate correct outputs to go in the Dockerfile grading container

python3 fsmain.py < hw2_2023_test1.in > correct_hw2_2023_test1.out
python3 fsmain.py < hw2_2023_test2.in > correct_hw2_2023_test2.out
python3 fsmain.py < hw2_2023_test3.in > correct_hw2_2023_test3.out
python3 fsmain.py < hw2_2023_test4.in > correct_hw2_2023_test4.out
python3 fsmain.py -bs 256 -nb 256 -is 32 -ni 32 < hw2_2023_test5.in > correct_hw2_2023_test5.out
python3 fsmain.py -bs 256 -nb 256 -is 32 -ni 32 < hw2_2023_test6.in > correct_hw2_2023_test6.out
python3 fsmain.py -bs 256 -nb 256 -is 32 -ni 32 < hw2_2023_test7.in > correct_hw2_2023_test7.out


