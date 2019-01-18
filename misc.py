import config

def clip_trips_to_window(trips):
	"""Remove trips outside a defined time window (set in config.py)."""
	to_remove = []
	for i, trip in enumerate(trips):
		if ( 
			trip.arrive.time() > config.window_end_time or 
			trip.depart.time() < config.window_start_time 
		):
			to_remove.append(i)
	for i in reversed(to_remove):
		del trips[i]
	#print('\t',len(to_remove),'trips removed from window')

def remove_premature_departures(trips):
	"""If a trip departs earlier but gets in later than another trip it is 
	suboptimal and needs to be removed."""
	starting_length = len(trips)
	# Sort by arrival, then search for trips not also sorted by departure
	trips.sort(key = lambda x: x.arrive_ts) # arrival, first to last
	fully_sorted = False # starting assumption
	while not fully_sorted:
		for i, trip in enumerate(trips):
			# if departure is before that of earlier-arriving trip
			if i > 0 and trip.depart_ts <= trips[i-1].depart_ts:
				trips.pop(i)
				continue
		fully_sorted = True 
	#print('\t',starting_length - len(trips),'suboptimal trips removed')
