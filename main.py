# tentative analysis script for routing paper

from OD import OD
import csv

# get a list of all ODs from file
all_locations = {}
with open('ODs.csv') as f:
	reader = csv.DictReader(f)
	for r in reader:
		all_locations[r['uid']] = dict(r)

# read in a list of prespecified pairs
ODs = []
with open('1_od.csv') as f:
	reader = csv.DictReader(f)
	for r in reader:
		ODs.append( OD(
			all_locations[ r['o'] ], 
			all_locations[ r['d'] ] 
		) )

# write out a summary file
with open('summary.csv','w+') as f:
	fieldnames = [
		'oid','did',
		'sched_ent','retro_ent',
		'sched_it_n','retro_it_n' ]
	writer = csv.DictWriter(f,fieldnames=fieldnames)
	writer.writeheader()
	for od in ODs:
		data_dict = {
			'oid':od.orig['uid'],
			'did':od.dest['uid'],
			'sched_ent':od.sched_entropy,
			'retro_ent':od.retro_entropy,
			'sched_it_n':len(od.sched_itins),
			'retro_it_n':len(od.retro_itins)
		}
		writer.writerow(data_dict)
