# tentative analysis script for routing paper

import os, csv
from datetime import datetime, time
from pytz import timezone
from pprint import pprint
input_dir = '/home/nate/dissdata/routing/'
localTime = timezone('America/Toronto')

class Trip(object):
	"""one shortest trip"""
	def __init__(self,depart,arrive,itin):
		self.depart = localTime.localize( datetime.fromtimestamp(float(depart)) )
		self.arrive = localTime.localize( datetime.fromtimestamp(float(arrive)) )
		self.itinerary = itin # string from otp script
		
	def __repr__(self):
		return str(self.depart.time())

	@property
	def routes(self):
		"""return an ordered list of routes only, e.g. ['47','506']"""
		segs = self.itinerary.split(',')
		routes = [ s[1:] for s in segs if s[0] == 'r' ]
		# now check for a route following itself
		if len(routes) <= 1 or len(routes) == len(set(routes)):
			return routes
		else: # else cleaning is necessary
			cleaned_routes = [routes[0]]
			for i, route in enumerate(routes):
				if i > 0 and route != routes[i-1]:
					cleaned_routes.append(route)
			return cleaned_routes

	@property
	def duration(self):
		"""length of trip in minutes"""
		return (self.arrive-self.depart).total_seconds() / 60.0


class OD(object):
	"""An O->D pair"""
	def __init__(self,origin,dest):
		"""origin and dest are dictionaries of the values from the ODs.csv file"""
		self.orig = origin
		self.dest = dest
		self.sched_trips, self.retro_trips = self.get_all_trips()
		self.remove_suboptimal_trips()
		self.remove_trips_outside_window()
		print( len(self.sched_trips),len(self.retro_trips) )
#		pprint(self.shares(),width=2)


	def get_all_trips(self):
		"""check all possible files for trips data"""
		sched_trips = []
		retro_trips = []
		# directories to check
		directories = ['sched','17476','17477','17478','17479','17480']
		for d in directories:
			fpath = input_dir+d+'/'+self.orig['uid']+'/'+self.dest['uid']+'.csv'
			if os.path.exists(fpath):
				if d == 'sched':
					sched_trips.extend( self.get_trips(fpath) )
				else:
					retro_trips.extend( self.get_trips(fpath) )
		return sched_trips, retro_trips

	def get_trips(self,csvpath):
		"""return a list of parsed trips from this CSV file"""
		with open(csvpath) as f:
			reader = csv.DictReader(f)
			return [ Trip(r['depart'],r['arrive'],r['itinerary']) for r in reader ]


	def remove_trips_outside_window(self):
		"""clip to trips inside a defined daytime window"""
		start = time(6,30,0) # h,m,s; 6:30am
		end = time(22,0,0) # h,m,s;  10:00pm
		for trips in [self.sched_trips,self.retro_trips]:
			to_remove = []
			for i, trip in enumerate(trips):
				if trip.depart.time() > end or trip.arrive.time() < start:
					to_remove.append(i)
			for i in reversed(to_remove):
				del trips[i]
			print('\t',len(to_remove),'trips removed from window')

	def remove_suboptimal_trips(self):
		"""If a trip departs earlier but gets in later than another trip it is 
		suboptimal and needs to be removed. Do this for both scheduled and 
		retrospective trips."""
		for trips in [self.sched_trips,self.retro_trips]:
			bad_trips = []
			for i, t1 in enumerate(trips):
				for t2 in trips:
					if t1.depart < t2.depart and t1.arrive > t2.arrive:
						bad_trips.append(i)
			for i in reversed(bad_trips):
				trips.pop(i)
			print('\t',len(bad_trips),'suboptimal trips removed')
		
	def shares(self):
		"""proportions of fastest trip itineraries"""
		itins = {}
		total_time = 0
		for i, trip in enumerate(self.trips):
			routes = ';'.join(trip.routes)
			if i == 0:
				from_prev = 0 
			else:
				from_prev = (trip.depart - self.trips[i-1].depart).total_seconds()
			total_time += from_prev
			if routes not in itins:
				itins[routes] = { 'count':1, 'time':from_prev }
			else:
				itins[routes]['count'] += 1
				itins[routes]['time'] += from_prev
		for key in itins:
			itins[key]['time'] = itins[key]['time'] / total_time
		return itins


# get a list of ODs from file
with open('personal-ODs.csv') as f:
	reader = csv.DictReader(f)
	locations = [ dict(r) for r in reader ]

# loop over OD combinations
ODs = []
for o in locations:
	for d in locations:
		if o['uid'] == d['uid']: continue
		ODs.append( OD(o,d) )

