import os, csv
from random import shuffle

# where are the things?
OD_file		= 'data/ODs.csv'
sample_file	= 'data/1k_od_sample.csv'

# read in the OD location data
points = {}
with open(OD_file) as csvfile:
	reader = csv.DictReader(csvfile, delimiter=',')
	for r in reader:
		points[int(r['uid'])] = {'lat':float(r['lat']),'lon':float(r['lon'])}

# read in the early sample
ksamp = []
with open(sample_file) as csvfile:
	reader = csv.DictReader(csvfile, delimiter=',')
	for r in reader:
		ksamp.append( ( int(r['o']), int(r['d']) ) )

# make a list of OD's not already in sample
other_ODs = []
for oid in points.keys():
	for did in points.keys():
		if oid == did: continue
		if (oid,did) in ksamp: continue
		other_ODs.append( (oid,did) )

print(len(other_ODs),'pairs remain')
shuffle(other_ODs)

with open('data/other_sample.csv','w+') as outfile:
	outfile.write('o,d')
	for o,d in other_ODs:
		outfile.write('\n{},{}'.format(o,d))
