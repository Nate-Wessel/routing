# this script iterates over a selection of OD pairs producing
#	1) OD level stats
#	2) OD-departure-time level departures for the three route methods

import csv
import config
from OD import OD

# open files for writing output
with open('data/summary.csv','w+') as f1, open('data/all_times.csv','w+') as f2:
	# OD level outputs
	fieldnames = [ 'i','o','d','azimuth','arc','weight','sched_ent','retro_ent',
		'sched_it_n','retro_it_n' ]
	od_writer = csv.DictWriter(f1,fieldnames=fieldnames)
	od_writer.writeheader()
	# OD - time level outputs
	fieldnames = [ 'o','d','departure','hour','hab','real','any' ]
	times_writer = csv.DictWriter(f2,fieldnames=fieldnames)
	times_writer.writeheader()

	# read input from a file
	with open('data/1k_od_sample.csv') as f3:
		reader = csv.DictReader(f3)
		for r in reader:
			# construct the OD
			od = OD( r['o'], r['d'] )
			# add attributes to output file
			od_writer.writerow({
				'i':r['i'], 'o':r['o'], 'd':r['d'],
				'azimuth':r['azimuth'], 'arc':r['arc'], 'weight':r['weight'],
				'sched_ent':od.sched_entropy,
				'retro_ent':od.retro_entropy,
				'sched_it_n':len(od.alter_itins('sched')),
				'retro_it_n':len(od.alter_itins('retro'))
			})
			f1.flush()
			# calculate travel times for the OD
			habit_times = od.travel_times('habit')
			real_times = od.travel_times('real')
			any_times = od.travel_times('any')
			i = 0
			while i < len(habit_times):
				times_writer.writerow({
					'o':r['o'], 'd':r['d'],
					'departure':habit_times[i].unix_departure,
					'hour':habit_times[i].departure_hour,
					'hab':habit_times[i].minutes_travel,
					'real':real_times[i].minutes_travel,
					'any':any_times[i].minutes_travel
				})
				i += 1
