import pytz
from datetime import datetime, timedelta
import config
from itinerary import Itinerary
from departure import Departure

# MANIPULATION OF TRIP VECTORS

def sample_times():
	"""Return a list of moments within the configured time window from which 
	travel times will be measured. Returns a list of datetimes."""
	the_times = []
	day = config.window_start_date
	while day <= config.window_end_date:
		# times from start of window on day to end of window 
		time = config.tz.localize( datetime.combine( 
			day, config.window_start_time 
		) )
		end_time = config.tz.localize( datetime.combine( 
			day, config.window_end_time 
		) )
		while time < end_time: # While still in the time window
			the_times.append( time )
			time += timedelta(minutes=1)
		day += timedelta(days=1)
	return the_times
		

def clip_trips_to_window(trips):
	"""Remove trips departing outside a defined time window 
	(set in config.py)."""
	to_remove = []
	for i, trip in enumerate(trips):
		if ( # checking for GOOD trips 
			# departs inside window
			config.window_start_time <= trip.depart.time() <= config.window_end_time 
			# and departs within date range
			and trip.depart.date() >= config.window_start_date
			and trip.depart.date() <= config.window_end_date 
		): 
			pass
		else:
			to_remove.append(i)
	for i in reversed(to_remove):
		del trips[i]


def remove_premature_departures(trips):
	"""Trade waiting time for travel time, removing trips departing earlier than 
	need be for a given arrival. Modifies trips list in place. 
	   _depart------------arrive
		__depart--------------arrive
		__depart----------------arrive      <- remove
		_________depart----------arrive
		____depart------------------arrive  <- remove """
	# sort ascending by arrival 
	# then iteratively remove trips not also sorted by departure
	starting_length = len(trips) # for logging
	#
	trips.sort(key = lambda x: x.arrive_ts) # arrival, first to last
	i = 1
	while i < len(trips):
		# if departure is before that of earlier-arriving trip
		if trips[i].depart_ts <= trips[i-1].depart_ts: 
			trips.pop(i)
			continue
		i+=1
	# there should be no simultaneous departures
	assert len(set([t.depart_ts for t in trips])) == len(trips)


def summarize_paths(trips):
	"""Returns a list of itineraries sorted by preeminence."""
	# get a set of distinct Path objects. We have to use equality rather than 
	# hashing here. 
	itins = []
	# add all trips to the Itinerary each belongs to 
	for trip in trips:
		if trip.path not in itins:
			itins.append( Itinerary(trip.path) )
		i = itins.index(trip.path)
		itins[i].add_OTP_trip( trip )
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

