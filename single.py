# This is for getting detailed stats on a single OD, mainly for diagnostic tests
from OD import OD
import csv

# get a list of all ODs from file
all_locations = {}
with open('ODs.csv') as f:
	reader = csv.DictReader(f)
	for r in reader:
		all_locations[r['uid']] = dict(r)

# these need to be specified as strings
o = '12'
d = '316'
od = OD(all_locations[o], all_locations[d] )
