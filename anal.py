# tentative analysis script for routing paper

import os, csv
from datetime import datetime, time
from pytz import timezone
from pprint import pprint
input_dir = '/home/nate/dissdata/routing/sched/'
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
	def __init__(self,filepath):
		self.path = filepath # absolute path to CSV file
		self.trips = []
		with open(self.path, newline='') as f:
			reader = csv.DictReader(f)
			for r in reader:
				self.trips.append( Trip(r['depart'],r['arrive'],r['itinerary']) )
		self.remove_suboptimal_trips()
		self.remove_trips_outside_window()
		pprint(self.shares(),width=1)

	def remove_trips_outside_window(self):
		"""clip to trips inside a defined daytime window"""
		start = time(6,30,0) # h,m,s; 6:30am
		end = time(22,0,0) # h,m,s;  10:00pm
		to_remove = []
		for i, trip in enumerate(self.trips):
			if trip.depart.time() > end or trip.arrive.time() < start:
				to_remove.append(i)
		for i in reversed(to_remove):
			del self.trips[i]
		print('\t',len(to_remove),'trips removed from window')

	def remove_suboptimal_trips(self):
		"""If a trip departs earlier but gets in later than another trip it is 
		suboptimal and needs to be removed"""
		bad_trips = []
		for i, t1 in enumerate(self.trips):
			for t2 in self.trips:
				if t1.depart < t2.depart and t1.arrive > t2.arrive:
					bad_trips.append(i)
		for i in reversed(bad_trips):
			self.trips.pop(i)
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


# loop over available o->d csv files
for o in os.listdir(input_dir):
	for filename in os.listdir(input_dir+o):
		csv_path = input_dir+o+'/'+filename
		d = filename[:-4]
		# only look at home and work for now
		selected = ('12','316','453')
		if o not in selected or d not in selected:
			continue
		print(o+'->'+d)
		# parse the file
		OD(csv_path)

