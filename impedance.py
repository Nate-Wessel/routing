# ACCESS AND IMPEDANCE FUNCTIONS
import math, config, db, triptools
import datetime as dt

class Departure:
	"""Departure, at a particular time, using a particular method."""
	def __init__(self,departure,travel_time):
		self.departure_time = departure
		self.travel_time = travel_time
	def __repr__(self):
		return 'dep:'+str(self.departure_time)+'tt:'+str(self.travel_time)
	@property
	def unix_departure(self):
		return self.departure_time.timestamp()
	@property
	def minutes_travel(self):
		if self.travel_time:
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
	worst_case = Departure(dt.datetime(2017,1,1),dt.timedelta(days=9999))
	current_best_times = [ worst_case ]
	# look up times on all viable itineraries, keeping the best times
	for itin in OD.alter_itins('retro'):
		trips = itin.get_trips()
		triptools.clip_trips_to_window(trips)
		times = triptools.trips2times(trips,itin.walk_time)
		if mean_travel_time(times) < mean_travel_time(current_best_times):
			current_best_times = times
			habit_itin = itin
	if habit_itin:
		#print('habit itin:',habit_itin)
		return current_best_times


def realtime_times(OD):
	"""Try to minimize initial wait times by taking the next-departing 
	itinerary. May walk if walking is shorter than waiting."""
	walk_time = None
	possible_trips = []
	for itin in OD.alter_itins():
		if not walk_time and itin.is_walking: 
			walk_time = itin.walk_time
		else: # itin has transit
			possible_trips.extend( itin.get_trips() )
	# if we have only walking, then all trips will be walking, full stop
	if walk_time and len(OD.alter_itins()) == 1:
		return triptools.trips2times([],walk_time)
	triptools.clip_trips_to_window(possible_trips)
	# the following commented line is the only difference between this and any-route
	# triptools.remove_premature_departures(possible_trips)
	return triptools.trips2times(possible_trips,walk_time)


def optimal_times(OD):
	"""Return a set of sampled travel times which are as fast as possible, and 
	indifferent to route choice. This is the status quo."""
	walk_time = None
	all_possible_trips = []
	for itin in OD.alter_itins():
		if not walk_time and itin.is_walking: 
			walk_time = itin.walk_time
		else: # itin has transit
			all_possible_trips.extend( itin.get_trips() )
	# if we have only walking, then all trips will be walking, full stop
	if walk_time and len(OD.alter_itins()) == 1:
		return triptools.trips2times([],walk_time)
	triptools.clip_trips_to_window(all_possible_trips)
	# the following line is the only difference between this and realtime
	triptools.remove_premature_departures(all_possible_trips)
	return triptools.trips2times(all_possible_trips,walk_time)


def mean_travel_time(departure_list):
	"""Mean travel time from a list of departures"""
	# convert to seconds, take the mean, return a timedelta, ignoring None's
	sec_list = [ d.travel_time.total_seconds() for d in departure_list if d.travel_time]
	return dt.timedelta( seconds=(sum(sec_list)/len(departure_list)) )

