#!/bin/sh

# test 1
t=1
python3 blockserver.py -nb 256 -bs 128 -port 8000  1> temp.out 2> temp.err &
sleep 3
server_pid=`ps -ef | grep "python3 blockserver.py" | grep -v "grep" | awk '{print $2}'`
if [ "$server_pid" ]
then
  python3 fsmain_hw4.py -port 8000 -cid 0 < hw4_2023_test$t.in > correct_hw4_2023_test$t.out
fi
kill $server_pid
rm temp.out temp.err
sleep 3


# test 2
t=2
python3 blockserver.py -nb 256 -bs 128 -port 8000 -delayat 10  1> temp.out 2> temp.err &
sleep 3
server_pid=`ps -ef | grep "python3 blockserver.py" | grep -v "grep" | awk '{print $2}'`
if [ "$server_pid" ]
then
  python3 fsmain_hw4.py -port 8000 -cid 0 < hw4_2023_test$t.in > correct_hw4_2023_test$t.out
fi
kill $server_pid
rm temp.out temp.err
sleep 3


# test 3
t=3
python3 blockserver.py -nb 256 -bs 128 -port 8000 1> temp.out 2> temp.err &
sleep 3
server_pid=`ps -ef | grep "python3 blockserver.py" | grep -v "grep" | awk '{print $2}'`
if [ "$server_pid" ]
then
  touch c0_shell
  touch c1_shell
  tail -f c0_shell | python3 fsmain_hw4.py -port 8000 -cid 0 > hw4_2023_test$t._c0.out &
  sleep 3
  tail -f c1_shell | python3 fsmain_hw4.py -port 8000 -cid 1 > hw4_2023_test$t._c1.out &
  sleep 3
  cat hw4_2023_test$t.in | while read shell_line
  do
    echo "${shell_line#*:}" >> c${shell_line%:*}_shell
    sleep 3
  done
  rm c0_shell c1_shell
fi
kill $server_pid
tail_pid=`ps -ef | grep "tail" | grep -v "grep" | awk '{print $2}'`
kill $tail_pid
tail_pid=`ps -ef | grep "tail" | grep -v "grep" | awk '{print $2}'`
kill $tail_pid
rm temp.out temp.err
sleep 3
cp hw4_2023_test$t._c0.out correct_hw4_2023_test$t.out
cat hw4_2023_test$t._c1.out >> correct_hw4_2023_test$t.out
rm hw4_2023_test$t._c0.out hw4_2023_test$t._c1.out


# test 4
t=4
python3 blockserver.py -nb 256 -bs 256 -port 8000 1> temp.out 2> temp.err &
sleep 3
server_pid=`ps -ef | grep "python3 blockserver.py" | grep -v "grep" | awk '{print $2}'`
if [ "$server_pid" ]
then
  touch c0_shell
  touch c1_shell
  tail -f c0_shell | python3 fsmain_hw4.py -bs 256 -nb 256 -is 32 -ni 32 -port 8000 -cid 0 > hw4_2023_test$t._c0.out &
  sleep 3
  tail -f c1_shell | python3 fsmain_hw4.py -bs 256 -nb 256 -is 32 -ni 32 -port 8000 -cid 1 > hw4_2023_test$t._c1.out &
  sleep 3
  cat hw4_2023_test$t.in | while read shell_line
  do
    echo "${shell_line#*:}" >> c${shell_line%:*}_shell
    sleep 3
  done
  rm c0_shell c1_shell
fi
kill $server_pid
tail_pid=`ps -ef | grep "tail" | grep -v "grep" | awk '{print $2}'`
kill $tail_pid
tail_pid=`ps -ef | grep "tail" | grep -v "grep" | awk '{print $2}'`
kill $tail_pid
rm temp.out temp.err
sleep 3
cp hw4_2023_test$t._c0.out correct_hw4_2023_test$t.out
cat hw4_2023_test$t._c1.out >> correct_hw4_2023_test$t.out
rm hw4_2023_test$t._c0.out hw4_2023_test$t._c1.out


# test 5
t=5
python3 blockserver.py -nb 256 -bs 128 -port 8000 -delayat 30 1> temp.out 2> temp.err &
sleep 3
server_pid=`ps -ef | grep "python3 blockserver.py" | grep -v "grep" | awk '{print $2}'`
if [ "$server_pid" ]
then
  touch c0_shell
  touch c1_shell
  tail -f c0_shell | python3 fsmain_hw4.py -port 8000 -cid 0 > hw4_2023_test$t._c0.out &
  sleep 15
  tail -f c1_shell | python3 fsmain_hw4.py -port 8000 -cid 1 > hw4_2023_test$t._c1.out &
  sleep 15
  cat hw4_2023_test$t.in | while read shell_line
  do
    echo "${shell_line#*:}" >> c${shell_line%:*}_shell
    sleep 15
  done
  rm c0_shell c1_shell
fi
kill $server_pid
tail_pid=`ps -ef | grep "tail" | grep -v "grep" | awk '{print $2}'`
kill $tail_pid
tail_pid=`ps -ef | grep "tail" | grep -v "grep" | awk '{print $2}'`
kill $tail_pid
rm temp.out temp.err
sleep 3
cp hw4_2023_test$t._c0.out correct_hw4_2023_test$t.out
cat hw4_2023_test$t._c1.out >> correct_hw4_2023_test$t.out
rm hw4_2023_test$t._c0.out hw4_2023_test$t._c1.out


# test 6
t=6
python3 blockserver.py -nb 256 -bs 128 -port 8000 1> temp.out 2> temp.err &
sleep 3
server_pid=`ps -ef | grep "python3 blockserver.py" | grep -v "grep" | awk '{print $2}'`
if [ "$server_pid" ]
then
  touch c0_shell
  touch c1_shell
  tail -f c0_shell | python3 fsmain_hw4.py -port 8000 -cid 0 > hw4_2023_test$t._c0.out &
  sleep 3
  tail -f c1_shell | python3 fsmain_hw4.py -port 8000 -cid 1 > hw4_2023_test$t._c1.out &
  sleep 3
  cat hw4_2023_test$t.in | while read shell_line
  do
    echo "${shell_line#*:}" >> c${shell_line%:*}_shell
    sleep 3
  done
  rm c0_shell c1_shell
fi
kill $server_pid
tail_pid=`ps -ef | grep "tail" | grep -v "grep" | awk '{print $2}'`
kill $tail_pid
tail_pid=`ps -ef | grep "tail" | grep -v "grep" | awk '{print $2}'`
kill $tail_pid
rm temp.out temp.err
sleep 3
cp hw4_2023_test$t._c0.out correct_hw4_2023_test$t.out
cat hw4_2023_test$t._c1.out >> correct_hw4_2023_test$t.out
rm hw4_2023_test$t._c0.out hw4_2023_test$t._c1.out


# test 7
t=7
python3 blockserver.py -nb 256 -bs 128 -port 8000 1> temp.out 2> temp.err &
sleep 3
server_pid=`ps -ef | grep "python3 blockserver.py" | grep -v "grep" | awk '{print $2}'`
if [ "$server_pid" ]
then
  touch c0_shell
  touch c1_shell
  tail -f c0_shell | python3 fsmain_hw4.py -port 8000 -cid 0 > hw4_2023_test$t._c0.out &
  sleep 3
  tail -f c1_shell | python3 fsmain_hw4.py -port 8000 -cid 1 > hw4_2023_test$t._c1.out &
  sleep 3
  cat hw4_2023_test$t.in | while read shell_line
  do
    echo "${shell_line#*:}" >> c${shell_line%:*}_shell
    sleep 3
  done
  rm c0_shell c1_shell
fi
kill $server_pid
tail_pid=`ps -ef | grep "tail" | grep -v "grep" | awk '{print $2}'`
kill $tail_pid
tail_pid=`ps -ef | grep "tail" | grep -v "grep" | awk '{print $2}'`
kill $tail_pid
rm temp.out temp.err
sleep 3
cp hw4_2023_test$t._c0.out correct_hw4_2023_test$t.out
cat hw4_2023_test$t._c1.out >> correct_hw4_2023_test$t.out
rm hw4_2023_test$t._c0.out hw4_2023_test$t._c1.out


# test 8
t=8
python3 blockserver.py -nb 256 -bs 256 -port 8000 1> temp.out 2> temp.err &
sleep 3
server_pid=`ps -ef | grep "python3 blockserver.py" | grep -v "grep" | awk '{print $2}'`
if [ "$server_pid" ]
then
  touch c0_shell
  touch c1_shell
  tail -f c0_shell | python3 fsmain_hw4.py -bs 256 -nb 256 -is 32 -ni 32 -port 8000 -cid 0 > hw4_2023_test$t._c0.out &
  sleep 3
  tail -f c1_shell | python3 fsmain_hw4.py -bs 256 -nb 256 -is 32 -ni 32 -port 8000 -cid 1 > hw4_2023_test$t._c1.out &
  sleep 3
  cat hw4_2023_test$t.in | while read shell_line
  do
    echo "${shell_line#*:}" >> c${shell_line%:*}_shell
    sleep 3
  done
  rm c0_shell c1_shell
fi
kill $server_pid
tail_pid=`ps -ef | grep "tail" | grep -v "grep" | awk '{print $2}'`
kill $tail_pid
tail_pid=`ps -ef | grep "tail" | grep -v "grep" | awk '{print $2}'`
kill $tail_pid
rm temp.out temp.err
sleep 3
cp hw4_2023_test$t._c0.out correct_hw4_2023_test$t.out
cat hw4_2023_test$t._c1.out >> correct_hw4_2023_test$t.out
rm hw4_2023_test$t._c0.out hw4_2023_test$t._c1.out
