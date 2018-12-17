# tentative analysis script for routing paper

import os, csv
from datetime import datetime
input_dir = '/home/nate/dissdata/routing/sched/'

class Trip(object):
	"""one shortest trip"""
	def __init__(self,depart,arrive,itin):
		self.depart = datetime.utcfromtimestamp(float(depart))
		self.arrive = datetime.utcfromtimestamp(float(arrive))
		self.itinerary = itin # string from otp script
		
	def __repr__(self):
		return str(self.depart.time())

	@property
	def routes(self):
		"""return an ordered list of routes only, e.g. ['47','506']"""
		segs = self.itinerary.split(',')
		return [ s[1:] for s in segs if s[0] == 'r' ]

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
		self.check_for_suboptimal_trips()
		print(self.portions())

	def check_for_suboptimal_trips(self):
		"""If a trip departs earlier but gets in later than another trip it is 
		suboptimal and needs to be removed"""
		bad_trips = []
		for i, t1 in enumerate(self.trips):
			for t2 in self.trips:
				if t1.depart < t2.depart and t1.arrive > t2.arrive:
					bad_trips.append(i)
		for i in reversed(bad_trips):
			self.trips.pop(i)
		print(len(bad_trips),'suboptimal trips removed')
		
	def portions(self):
		"""distribution of trips"""
		itins = {}
		for i, trip in enumerate(self.trips):
			routes = ';'.join(trip.routes)
			if i == 0:
				from_prev = 0 
			else:
				from_prev = (trip.depart - self.trips[i-1].depart).total_seconds()
			if routes not in itins:
				itins[routes] = { 'count':1, 'time':from_prev }
			else:
				itins[routes]['count'] += 1
				itins[routes]['time'] += from_prev
		return itins


# loop over available o->d csv files
for o in os.listdir(input_dir):
	for filename in os.listdir(input_dir+o):
		csv_path = input_dir+o+'/'+filename
		d = filename[:-4]
		# only look at home and work for now
		if o not in ('12','316') or d not in ('12','316'):
			continue
		print(o+'->'+d)
		# parse the file
		OD(csv_path)

