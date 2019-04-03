import math, config, db, triptools
import datetime as dt

class Departure:
	"""Departure, at a particular time, using a particular method."""
	def __init__(self,from_time,trip=None,walk_itin=None):
		"""
		from_time: when the departure is starting from, if not departing
		trip: trip object assigned to this departure
		walk_itin: an alternative walking itinerary
		"""
		self.departure_time = from_time
		self.trip = trip
		self.walk_time = None
		self.path = None
		if trip: 
			self.path = trip.path
		elif walk_itin: 
			self.walk_time = walk_itin.walk_time
			self.path = walk_itin
		else: pass 	# no way of getting to the destination

	def __repr__(self):
		rep = 'Departure from:{}'.format(self.departure_time.time())
		if self.trip:
			rep += ',depart at:{}'.format(self.trip.depart.time())
			rep += ',arrive at:{}\n'.format(self.trip.arrive.time())
		return rep

	@property
	def unix_departure(self):
		"""unix departure timestamp"""
		return int(self.departure_time.timestamp())

	@property
	def minutes_travel(self):
		"""travel time in minutes"""
		if self.trip and self.trip.arrive.date() == self.departure_time.date():
			tt = self.trip.arrive - self.departure_time
			return round( tt.total_seconds()/60., 3 )
		elif self.walk_time:
			return round( self.walk_time.total_seconds()/60., 3 )
		else: 
			return None

	@property
	def departure_hour(self):
		"""hour of the departure (for binning into hours)"""
		return int(self.departure_time.hour)

	@property
	def travel_time(self):
		"""Timedelta travel time or None. Trip must be on same day as departure 
		if it uses a transit trip."""
		if self.trip and self.trip.arrive.date() == self.departure_time.date():
			return self.trip.arrive - self.departure_time
		elif self.walk_time:
			return self.walk_time

#	@property
#	def wait_duration(self):
#		"""time spent waiting to depart, not including walking"""
#		if self.trip:
#			return self.trip.depart - self.departure_time
		
	@property
	def minutes_before_boarding(self):
		"""Minutes spent waiting or walking before boarding the first vehicle. If 
		this is a walking only trip then this is equal to the walk time."""
		assert self.trip or self.walk_time
		if self.trip:
			td = self.trip.first_boarding_time - self.departure_time
			return round(td.total_seconds()/60.,3)
		elif self.walk_itin:
			return round(self.walk_time.total_seconds()/60.,3)



