# tentative analysis script for routing paper

from OD import OD
import csv

# get a list of ODs from file
with open('personal-ODs.csv') as f:
	reader = csv.DictReader(f)
	locations = [ dict(r) for r in reader ]

# loop over OD combinations
ODs = []
for o in locations:
	for d in locations:
		if o['uid'] == d['uid']: continue
		ODs.append( OD(o,d) )

