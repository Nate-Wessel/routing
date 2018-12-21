# tentative analysis script for routing paper

import os, csv
from datetime import datetime as dt
from datetime import time
from pytz import timezone
from pprint import pprint
from math import log
input_dir = '/home/nate/dissdata/routing/'
localTime = timezone('America/Toronto')

class Trip(object):
	"""one shortest trip"""
	def __init__(self,depart,arrive,itin):
		# times in unix epoch
		self.depart = float(depart)
		self.arrive = float(arrive)
		self.itinerary = itin # string from otp script
		
	def __repr__(self):
		local_datetime = localTime.localize( 
			dt.fromtimestamp(
				self.depart ) )
		return str( local_datetime.time() )

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
		return ( self.arrive - self.depart ) / 60.0


class OD(object):
	"""An O->D pair"""
	def __init__(self,origin,dest):
		"""origin and dest are dictionaries of the values from the ODs.csv file"""
		self.orig = origin
		self.dest = dest
		# read in the trip itineraries
		self.sched_trips = self.get_all_trips('sched')
		self.retro_trips = self.get_all_trips('retro')
		# clean out irrelevant trips for both datasets
		self.remove_trips_outside_window()
		self.remove_suboptimal_trips()
		# summarize itinerary data
		self.sched_itins = self.summarize_itineraries(self.sched_trips)
		self.retro_itins = self.summarize_itineraries(self.retro_trips)
		# print summary info, including entropy
		print(self)

	def __repr__(self):
		name = self.orig['nomen']+' -> '+self.dest['nomen']
		entropy =  '\n\tentropy-s:{},r:{}'.format(
			round(self.entropy(self.sched_itins),2),
			round(self.entropy(self.retro_itins),2)
		)
		return( name+' '+entropy )

	def entropy(self,itineraries):
		"""shannon entropy of the itinerary probability distribution"""
		entropy = 0
		for itin in itineraries:
			probability = itineraries[itin]['time']
			entropy += probability * log(probability,2)
		return - entropy

	def get_all_trips(self,dataset):
		"""Check files for trips data and read it into a list."""
		# directories to check
		if dataset == 'sched': 
			directories = ['sched'] 
		elif dataset == 'retro': 
			directories = ['17476','17477','17478','17479','17480']
		trips = []
		for d in directories:
			csvpath = input_dir+d+'/'+self.orig['uid']+'/'+self.dest['uid']+'.csv'
			if not os.path.exists(csvpath): continue			
			with open(csvpath) as f:
				reader = csv.DictReader(f)	
				trips.extend( 
					[ Trip(r['depart'],r['arrive'],r['itinerary']) for r in reader ]
				)
		return trips

	def remove_trips_outside_window(self):
		"""clip to trips inside a defined daytime window"""
		start = time(6,30,0) # h,m,s; 6:30am
		end = time(22,0,0) # h,m,s;  10:00pm
		for trips in [self.sched_trips,self.retro_trips]:
			to_remove = []
			for i, trip in enumerate(trips):
				arrival = localTime.localize(dt.fromtimestamp(trip.arrive)).time()
				departure = localTime.localize(dt.fromtimestamp(trip.depart)).time()
				if departure > end or arrival < start:
					to_remove.append(i)
			for i in reversed(to_remove):
				del trips[i]
			#print('\t',len(to_remove),'trips removed from window')

	def remove_suboptimal_trips(self):
		# TODO make sure this actually does what it is supposed to
		"""If a trip departs earlier but gets in later than another trip it is 
		suboptimal and needs to be removed. Do this for both scheduled and 
		retrospective trips."""
		for trips in [self.sched_trips,self.retro_trips]:
			trips.sort(key = lambda x: x.arrive)
			#trips.sort() # by arrival
			bad_trips = []
			for i, trip in enumerate(trips):
				# first one is good by definition
				if i == 0: continue
				if trip.depart < trips[i-1].depart:
					bad_trips.append(i)
			for i in reversed(bad_trips):
				trips.pop(i)
			#print('\t',len(bad_trips),'suboptimal trips removed')
		
	def summarize_itineraries(self,trips):
		"""proportions of fastest trip itineraries"""
		itins = {}
		total_time = 0
		for i, trip in enumerate(trips):
			routes = ';'.join(trip.routes)
			if i == 0:
				from_prev = 60 # default to 60 seconds to prevent p == 0
			else:
				from_prev = ( trip.depart - trips[i-1].depart )
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

