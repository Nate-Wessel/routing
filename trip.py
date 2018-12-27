from datetime import datetime as dt
from pytz import timezone
EST = timezone('America/Toronto')


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
		self.itinerary = itin # string from otp script
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

