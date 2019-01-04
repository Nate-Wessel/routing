from datetime import datetime as dt
from pytz import timezone
EST = timezone('America/Toronto')
import db
from itinerary import Itinerary

class Trip(object):
	"""one shortest trip"""
	def __init__(self,depart,arrive,itin):
		# unix timestamps
		self.depart_ts = float(depart)
		self.arrive_ts = float(arrive)
		# localized datetime's
		self.depart = EST.localize( dt.fromtimestamp( self.depart_ts ) )
		self.arrive = EST.localize( dt.fromtimestamp( self.arrive_ts ) )
		# 
		self.itinerary = Itinerary(itin) # string from otp script
		self.time_before = 0 # time from previous fastest trip

	def __repr__(self):
		"""just print the departure time"""
		return str( self.local_time('d') )

	@property
	def itin_uid(self):
		"""string defining the itinerary"""
		return ';'.join(self.itinerary.collapsed_routes)

	@property
	def duration(self):
		"""length of trip in minutes"""
		return ( self.arrive_ts - self.depart_ts ) / 60.0

	def verify(self):
		"""Try to verify that this trip, or something close to it, exists in the 
		database."""
		# iterate over *route* segments
		time = self.depart_ts
		for i, step in enumerate( self.itinerary.segments ):
			expected_route = step['route']
			# Query the database about this supposed trip
			# pushing time forward from the departure to the arrival at the next stop
			( time, route_id ) = db.o2d_at( step['stop1'], step['stop2'], time + step['walk']/2.)
			# make sure we got some result
			if not route_id:
				print('\t',expected_route,'segment not confirmed')
				return
			if route_id != expected_route:
				print('\tdifferent route used:',route_id,'but expected',expected_route)
		# add time for walking to the final destination
		time += self.itinerary.final_walk / 2.
		print('\t', round(time-self.arrive_ts,2), self.depart_ts, self.arrive_ts, self.itinerary.original )

