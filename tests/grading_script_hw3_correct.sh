#!/bin/sh

# This is to generate correct outputs to go in the Dockerfile grading container

python3 fsmain_hw3.py < hw3_2023_test1.in > correct_hw3_2023_test1.out
python3 fsmain_hw3.py < hw3_2023_test2.in > correct_hw3_2023_test2.out
python3 fsmain_hw3.py < hw3_2023_test3.in > correct_hw3_2023_test3.out
python3 fsmain_hw3.py < hw3_2023_test4.in > correct_hw3_2023_test4.out
python3 fsmain_hw3.py < hw3_2023_test5.in > correct_hw3_2023_test5.out
python3 fsmain_hw3.py -bs 256 -nb 256 -is 32 -ni 32 < hw3_2023_test6.in > correct_hw3_2023_test6.out
python3 fsmain_hw3.py < hw3_2023_test7.in > correct_hw3_2023_test7.out
python3 fsmain_hw3.py < hw3_2023_test8.in > correct_hw3_2023_test8.out
python3 fsmain_hw3.py < hw3_2023_test9.in > correct_hw3_2023_test9.out
python3 fsmain_hw3.py -bs 256 -nb 256 -is 32 -ni 32 < hw3_2023_test10.in > correct_hw3_2023_test10.out
python3 fsmain_hw3.py < hw3_2023_test11.in > correct_hw3_2023_test11.out
python3 fsmain_hw3.py < hw3_2023_test12.in > correct_hw3_2023_test12.out


