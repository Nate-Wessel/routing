# tentative analysis script for routing paper

from OD import OD
import csv

# read in a list of prespecified pairs
ODs = []
with open('data/1k_od_sample.csv') as f:
	reader = csv.DictReader(f)
	for r in reader:
		ODs.append( OD( r['o'], r['d'] ) )

# write out a summary file
with open('data/summary.csv','w+') as f:
	fieldnames = [
		'oid','did',
		'sched_ent','retro_ent',
		'sched_it_n','retro_it_n' ]
	writer = csv.DictWriter(f,fieldnames=fieldnames)
	writer.writeheader()
	for od in ODs:
		data_dict = {
			'oid':od.orig,
			'did':od.dest,
			'sched_ent':od.sched_entropy,
			'retro_ent':od.retro_entropy,
			'sched_it_n':len(od.sched_itins),
			'retro_it_n':len(od.retro_itins)
		}
		writer.writerow(data_dict)
