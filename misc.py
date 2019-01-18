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

def summarize_itineraries(trips):
	"""Returns a list of itineraries sorted by prominence. Total time within 
	the time window spent as optimal next trip is assigned to itineraries as 
	a property."""
	# get a set of distinct itinerary objects
	unique_itins = set([trip.itinerary for trip in trips])
	# put this in a dict with initial counts
	counter = { it:{'time':0,'count':0} for it in unique_itins }
	# add times from trips to each 
	for trip in trips:
		counter[trip.itinerary]['time'] += trip.time_before
		counter[trip.itinerary]['count'] += 1
	# for each itinerary and it's counts
	for it in counter:
		it.time = counter[it]['time']
		it.count = counter[it]['count']
	# we now reconstruct this from the dict as a list of itineraries
	unique_itins =  [ it for it in counter ]
	# get total time in trips
	total_time = sum( [ it.time for it in unique_itins ] )
	# assign probabilities based on share of total time
	for it in unique_itins:
		it.prob = it.time / total_time
	# and sort by prob, highest first
	return sorted( unique_itins, key=lambda k: k.prob, reverse=True )
