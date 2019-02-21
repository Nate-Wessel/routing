# ACCESS AND IMPEDANCE FUNCTIONS
import math, config, db, triptools
import datetime as dt

class Departure:
	"""Departure, at a particular time, using a particular method."""
	def __init__(self,departure_time,trip=None):
		self.departure_time = departure_time
		# reference to the trip object used
		self.trip = trip

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
		if self.trip:
			tt = self.trip.arrive - self.departure_time
			return round( tt.total_seconds()/60., 3 )

	@property
	def departure_hour(self):
		"""hour of the departure (for binning into hours)"""
		return int(self.departure_time.hour)

	@property
	def travel_time(self):
		"""timedelta travel time or none"""
		if self.trip:
			return self.trip.arrive - self.departure_time

	@property
	def wait_duration(self):
		"""time spent waiting to depart, not including walking"""
		if self.trip:
			return self.trip.depart - self.departure_time
		
	@property
	def minutes_before_boarding(self):
		"""time spent waiting or walking before boarding the first vehicle"""
		td = self.trip.first_boarding_time - self.departure_time
		return round(td.total_seconds()/60.,3)

