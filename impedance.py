# ACCESS AND IMPEDANCE FUNCTIONS
import math, config, db, triptools
import datetime as dt

class Departure:
	"""Departure, at a particular time, using a particular method."""
	def __init__(self,departure,travel_time):
		self.departure_time = departure
		self.travel_time = travel_time
	def __repr__(self):
		return 'departure_at:'+str(self.departure_time)
	@property
	def unix_departure(self):
		return self.departure_time.timestamp()
	@property
	def minutes_travel(self):
		return round( self.travel_time.total_seconds()/60, 3 )
	@property
	def departure_hour(self):
		return self.departure_time.hour

def cum(td,theta=45):
	"""Cumulative accessibility function. Accepts a timedelta and returns a 
	binary measure. Theta is in minutes."""
	return 0 if td.total_seconds()/60. < theta else 1

def negexp(td,beta=30):
	"""Negative exponential distance decay function with parameter in minutes."""
	return math.exp( -( td.travel_time.total_seconds() / 60. / beta ) )

def habitual_times(OD):
	"""Return a set of travel times over the time window for the assumption that
	travellers consistently take the itinerary which minimizes mean travel
	time."""
	habit_itin = None
	current_best_times = [Departure(dt.datetime(2017,1,1),dt.timedelta(days=99))]
	# look up times on all viable itineraries, keeping the best times
	for itin in OD.alter_itins('retro'):
		if itin.is_walking:
			walk_time = dt.timedelta(
				seconds= itin.total_walk_distance/config.walk_speed )
			if seconds_walking <= mean_travel_time(current_best_times):
				current_best_times = [ seconds_walking ]
				habit_itin = itin
		else:
			# this trip involves transit and we need to look up trips in the DB
			trips = itin.get_trips()
			triptools.clip_trips_to_window(trips)
			times = triptools.trips2times(trips)
			if mean_travel_time(times) <= mean_travel_time(current_best_times):
				current_best_times = times
				habit_itin = itin
	if habit_itin:
		print('habit itin:',habit_itin)
		return current_best_times


def realtime_times(OD):
	"""Try to minimize initial wait times by taking the next-departing 
	itinerary. Can potentially walk if nothing coming."""
	walk_option = False
	possible_trips = []
	for itin in OD.alter_itins():
		if itin.is_walking:
			walk_option = True
			# don't look up a walking trip - we already know the travel time
			seconds_walking = itin.total_walk_distance / config.walk_speed
			walk_time = timedelta(seconds=seconds_walking)
		else:
			# not a walking itinerary
			trips = itin.get_trips()
			possible_trips.extend(trips)
	# now that we have trips from all itineraries
	if walk_option and len(OD.alter_itins()) == 1:
		return [ walk_time ]
	triptools.clip_trips_to_window(possible_trips)
	#  triptools.remove_premature_departures(possible_trips)
	if walk_option and len(OD.alter_itins()) > 1:
		return triptools.trips2times(possible_trips,walk_time)
	else:
		return triptools.trips2times(possible_trips)


def route_indifferent_times(OD):
	"""Return a set of sampled travel times which are as fast as possible, and 
	indifferent to route choice. This is the null hypothesis essentially."""
	possible_trips = []
	walk_option = False
	for itin in OD.alter_itins():
		# there should only be <= 1 walk option per OD
		if itin.is_walking:
			walk_option = True
			# don't look up a walking trip - we already know the travel time
			seconds_walking = itin.total_walk_distance / config.walk_speed
			walk_time = timedelta(seconds=seconds_walking)
		else: # not a walking itinerary
			trips = itin.get_trips()
			possible_trips.extend(trips)
	# now that we have trips from all itineraries
	if walk_option and len(OD.alter_itins()) == 1:
		return [ walk_time ]
	triptools.clip_trips_to_window(possible_trips)
	triptools.remove_premature_departures(possible_trips)
	if walk_option and len(OD.alter_itins()) > 1:
		return triptools.trips2times(possible_trips,walk_time)
	else:
		return triptools.trips2times(possible_trips)


def mean_travel_time(departure_list):
	"""Mean travel time from a list of departures"""
	# convert to seconds, take the mean, return a timedelta
	sec_list = [ tt.travel_time.total_seconds() for tt in departure_list ]
	return dt.timedelta( seconds=(sum(sec_list)/len(departure_list)) )

