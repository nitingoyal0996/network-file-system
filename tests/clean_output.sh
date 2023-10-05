#!/bin/sh

sed -i 's/\%/\%\n/g' $1 #adds a newline after a :
sed -i 's/\x0//g' $1 #removes all the zero characters
sed -i '/^$/d' $1 #removes all the blank lines
