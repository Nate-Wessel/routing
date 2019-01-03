from datetime import datetime as dt
from pytz import timezone
EST = timezone('America/Toronto')
import db

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
		self.itinerary = itin[1:-1] # string from otp script
		self.time_before = 0 # time from previous fastest trip
		# get an ordered list of routes only, e.g. ['47','506']
		segs = self.itinerary.split(',')
		routes = [ s[1:] for s in segs if s[0] == 'r' ]
		# now check for a route following itself
		if len(routes) <= 1 or len(routes) == len(set(routes)):
			self.routes = routes
		else: # else cleaning is necessary
			cleaned_routes = [routes[0]]
			for i, route in enumerate(routes):
				if i > 0 and route != routes[i-1]:
					cleaned_routes.append(route)
			self.routes = cleaned_routes

	def __repr__(self):
		"""just print the departure time"""
		return str( self.local_time('d') )

	@property
	def itin_uid(self):
		"""string defining the itinerary"""
		return ';'.join(self.routes)

	@property
	def duration(self):
		"""length of trip in minutes"""
		return ( self.arrive_ts - self.depart_ts ) / 60.0

	def verify(self):
		"""Try to verify that this trip, or something close to it, exists in the 
		database."""
		# iterate over *route* segments
		steps = self.itinerary.split(',')
#		print(steps)
		time = self.depart_ts
		for i, step in enumerate( steps ):
			if step[0] != 'r': 
				continue
			# make sure we know where stuff is
			assert steps[i-1][0] == 's' and steps[i+1][0] == 's'
			# get IDs of stops for boarding and disembarking
			stop1 = int(steps[i-1][1:].strip('_'))
			stop2 = int(steps[i+1][1:].strip('_'))
			expected_route = step[1:]
			# Query the database about this supposed trip
			# pushing time forward from the departure to the arrival at the next stop
			( time, route_id ) = db.o2d_at( stop1, stop2, time )
			# make sure we got some result
			if not route_id:
				print('\t',expected_route,'segment not confirmed')
				return
			if route_id != expected_route:
				print('\tdifferent route used:',route_id,'but expected',expected_route)
			# add time for walking to the next stop based on 
			# walking distance in meters if any
			if steps[i+2][0] == 'w':
				time += int(steps[i+2][1:]) / 1.5 # meters / mps = seconds required
		print('\t', round(time-self.arrive_ts,2) )

