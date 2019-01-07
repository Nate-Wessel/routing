# This is for getting detailed stats on a single OD, mainly for diagnostic tests
from OD import OD
import csv

# get a list of all ODs from file
all_locations = {}
with open('ODs.csv') as f:
	reader = csv.DictReader(f)
	for r in reader:
		all_locations[r['uid']] = dict(r)

# read in a list of prespecified pairs
with open('1_od.csv') as f:
	reader = csv.DictReader(f)
	for r in reader:
		OD(all_locations[ r['o'] ], all_locations[ r['d'] ] )
