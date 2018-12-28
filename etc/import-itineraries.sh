#!/bin/bash
DIR=/home/nate/dissdata/routing
FOLDERS=$DIR/*
for folder in $FOLDERS 
	do
		FILES=$folder/*
		for file in $FILES
			do
				echo "O:$(basename $folder), D:$(basename $file)"
				psql -d routing -c "COPY ttc_Sched (o,d,departure,arrival,itinerary) FROM '$file' CSV HEADER;"
			done
	done
