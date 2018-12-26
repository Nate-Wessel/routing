from datetime import datetime as dt
from pytz import timezone
localTime = timezone('America/Toronto')


class Trip(object):
	"""one shortest trip"""
	def __init__(self,depart,arrive,itin):
		# times in unix epoch
		self.depart = float(depart)
		self.arrive = float(arrive)
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
		return str( self.local_time('departure') )

	def local_time(self,dep_or_arr):
		if dep_or_arr in ['d','dep','depart','departure']:
			return localTime.localize( dt.fromtimestamp( self.depart ) ).time()
		elif dep_or_arr in ['a','arr','arrive','arrival']:
			return localTime.localize( dt.fromtimestamp( self.arrive ) ).time()
		else:
			return None

	def local_date(self,dep_or_arr):
		if dep_or_arr in ['d','dep','depart','departure']:
			return localTime.localize( dt.fromtimestamp( self.depart ) ).date()
		elif dep_or_arr in ['a','arr','arrive','arrival']:
			return localTime.localize( dt.fromtimestamp( self.arrive ) ).date()
		else:
			return None

	@property
	def itin_uid(self):
		"""string defining the itinerary"""
		return ';'.join(self.routes)

	@property
	def duration(self):
		"""length of trip in minutes"""
		return ( self.arrive - self.depart ) / 60.0
