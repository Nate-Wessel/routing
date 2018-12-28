#!/bin/bash
DIR=/home/nate/dissdata/routing/sched
FOLDERS=$DIR/*
for folder in $FOLDERS 
	do
		FILES=$folder/*.csv
		for file in $FILES
			do
				SIZE=$(stat -c%s $file)
				if [ $SIZE -lt 200 ]
				then 
					echo "$file $SIZE bytes"
				fi
			done
	done
