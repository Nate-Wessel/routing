# this script iterates over a selection of OD pairs producing
#	1) OD level stats
#	2) OD-departure-time level departures for the three route methods

import csv
from OD import OD

# open a file for writing output
with open('data/summary.csv','w+') as f:
	fieldnames = [
		'i','o','d','azimuth','arc',
		'sched_ent','retro_ent',
		'sched_it_n','retro_it_n' ]
	writer = csv.DictWriter(f,fieldnames=fieldnames)
	writer.writeheader()
	# open a file for reading input
	with open('data/1k_od_sample.csv') as f:
		reader = csv.DictReader(f)
		for r in reader:
			# construct the OD
			od = OD( r['o'], r['d'] )
			# add attributes to output file
			data_dict = {
				'i':r['i'], 'o':od.orig, 'd':od.dest,
				'azimuth':r['azimuth'], 'arc':r['arc'],
				'sched_ent':od.sched_entropy,
				'retro_ent':od.retro_entropy,
				'sched_it_n':len(od.alter_itins('sched')),
				'retro_it_n':len(od.alter_itins('retro'))
			}
			writer.writerow(data_dict)
