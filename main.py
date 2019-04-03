# this script iterates over a selection of OD pairs producing
#	1) OD level stats
#	2) OD-departure-time level departures for the three route methods

import csv
import config
from OD import OD

# open files for writing output
with open('data/untracked/od-stats.csv','w+') as f1, \
	open('data/untracked/times.csv','w+') as f2:
	# OD level outputs
	fieldnames = [ 'i','o','d','entropy','it_n' ]
	od_writer = csv.DictWriter(f1,fieldnames=fieldnames)
	od_writer.writeheader()
	# OD - time level outputs
	fieldnames = [ 'o','d','departure','hour','hab','real','any' ]
	times_writer = csv.DictWriter(f2,fieldnames=fieldnames)
	times_writer.writeheader()

	# read input from a file
	line_num = 0
	with open('data/sampled-ODs/1k.csv') as f3:
		reader = csv.DictReader(f3)
		for r in reader:
			line_num += 1 
			#if line_num <= 248: continue
			# construct the OD
			od = OD( r['o'], r['d'] )
			# add attributes to output file
			od_writer.writerow({
				'i':r['i'], 'o':r['o'], 'd':r['d'],
				'entropy':od.entropy,
				'it_n':len(od.alter_itins()),
			})
			f1.flush()
			# calculate travel times for the OD
			habit_times = od.habit_departures
			real_times = od.realtime_departures
			any_times = od.optimal_departures
			assert len(habit_times) == len(real_times) == len(any_times)
			i = 0
			while i < len(habit_times):
				# all departure times should line up
				assert habit_times[i].departure_time == real_times[i].departure_time
				assert real_times[i].departure_time == any_times[i].departure_time
				# any_time should be equal or lower than others
				if habit_times[i].travel_time:
					assert any_times[i].travel_time
					assert habit_times[i].travel_time >= any_times[i].travel_time
				if real_times[i].travel_time:
					assert real_times[i].travel_time >= any_times[i].travel_time
				times_writer.writerow({
					'o':r['o'], 'd':r['d'],
					'departure':habit_times[i].unix_departure,
					'hour':habit_times[i].departure_hour,
					'hab':habit_times[i].minutes_travel,
					'real':real_times[i].minutes_travel,
					'any':any_times[i].minutes_travel
				})
				i += 1
			print(line_num,':',od)
		
