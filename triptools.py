import pytz
from datetime import datetime, timedelta
import config
from itinerary import Itinerary
from impedance import Departure

# MANIPULATION OF TRIP VECTORS

def trips2times(trips,upper_bound=None):
	"""Take a vector of trips and return a vector of sampled travel times
	(timedeltas). Upper bound is used for limiting times by e.g. a worst case
	walking option"""
	travel_times = []
	# ensure trips are sorted by departure, ASC
	trips.sort(key = lambda x: x.depart_ts)
	# first only look at days (dates) where there is data
	for day in sorted(list(set([ trip.depart.date() for trip in trips ]))):
		# times from start of window on day to end of window 
		time = config.tz.localize( datetime.combine( 
			day, config.window_start_time ) )
		end_time = config.tz.localize( datetime.combine( 
			day, config.window_end_time ) )
		# iterate over minutes looking for arrival of next-departing trip
		i = 0
		while time < end_time and i < len(trips)-1:
			# While this trip departs in the past and i is still in range
			while i < len(trips)-1 and trips[i].depart <= time: 
				i += 1
			td = trips[i].arrive - time
			if upper_bound and td > upper_bound:
				td = upper_bound
			travel_times.append( Departure(time,td) )
			time += timedelta(minutes=1)
	return travel_times
		

def clip_trips_to_window(trips):
	"""Remove trips departing outside a defined time window 
	(set in config.py)."""
	to_remove = []
	for i, trip in enumerate(trips):
		if ( # checking for GOOD trips 
			# departs inside window
			config.window_start_time < trip.depart.time() < config.window_end_time 
			# and departs within date range
			and trip.depart.date() >= config.window_start_date
			and trip.depart.date() <= config.window_end_date 
		): 
			pass
		else:
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


def summarize_paths(trips):
	"""Returns a list of itineraries sorted by preeminence."""
	# get a set of distinct Path objects. We have to use equality rather than 
	# hashing here. 
	itins = []
	for trip in trips:
		if trip.path not in itins:
			# convert neew paths to Itineraries
			itins.append( Itinerary(trip.path) )
	# add times from trips to each 
	for trip in trips:
		i = itins.index(trip.path)
		itins[i].add_trip( trip )
	# get total time in trips
	total_time = sum( [ itin.total_time for itin in itins ] )
	# assign probabilities based on share of total time
	for itin in itins:
		itin.prob = itin.total_time / total_time
	# and sort by prob, highest first
	return sorted( itins, key=lambda k: k.prob, reverse=True )


def allocate_time(trips):
	"""Allocate the time (in seconds) for which this trip is the next, 
	clipping to the window used for removing trips."""
	# sort the trips by departure
	trips = sorted(trips, key=lambda k: k.depart) 
	dates_seen = set()
	for i, trip in enumerate(trips):
		if i == 0 or not trip.depart.date() in dates_seen:
			# trip is first of the day
			dates_seen |= {trip.depart.date()}
			# create a localized datetime 
			start_dt = config.tz.localize( datetime.combine(
				trip.depart.date(), config.window_start_time
			) )
			from_prev = (trip.depart - start_dt).total_seconds()
		else:
			# trip follows previous trip on this day 
			from_prev = (trip.depart - trips[i-1].depart).total_seconds()
		trip.time_before = from_prev

