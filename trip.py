from datetime import datetime as dt
import db, config
from itinerary import Itinerary
import pytz

class Trip(object):
	"""one shortest trip"""
	def __init__(self,depart,arrive,itin):
		# unix timestamps
		self.depart_ts = float(depart)
		self.arrive_ts = float(arrive)
		# localized datetime's
		self.depart = pytz.utc.localize( 
			dt.utcfromtimestamp(self.depart_ts) 
		).astimezone(config.tz)
		self.arrive = pytz.utc.localize( 
			dt.utcfromtimestamp(self.arrive_ts) 
		).astimezone(config.tz)
		# itin can either be an Itinerary object or a string (from OTP script)
		self.itinerary = itin if type(itin) == Itinerary else  Itinerary(itin)
		self.time_before = 0 # time from previous fastest trip

	def __repr__(self):
		"""just print the departure time"""
		return str( self.depart.time() )

	@property
	def duration(self):
		"""duration of trip as timedelta"""
		return self.arrive - self.depart

	def verify(self):
		"""Try to verify that this trip, or something close to it, exists in the 
		database."""
		# iterate over *route* segments
		time = self.depart_ts
		for i, step in enumerate( self.itinerary.segments ):
			expected_route = step['route']
			# Query the database about this supposed trip
			# pushing time forward from the departure to the arrival at the next stop
			( time, route_id ) = db.o2d_at( 
				step['stop1'], 
				step['stop2'], 
				time + step['walk']/config.walk_speed
			)
			# make sure we got some result
			if not route_id:
				print('\t',expected_route,'segment not confirmed')
				return
			if route_id != expected_route:
				print('\tdifferent route used:',route_id,'but expected',expected_route)
		# add time for walking to the final destination
		time += self.itinerary.final_walk / config.walk_speed
		diff_pct = (time-self.arrive_ts) / (self.arrive_ts-self.depart_ts)
		print('\t{:+.2%}'.format(diff_pct) , self.itinerary.original )

