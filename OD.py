from trip import Trip
import os, csv
from datetime import time
from math import log
input_dir = '/home/nate/dissdata/routing/'

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
		self.allocate_time(self.sched_trips)
		self.allocate_time(self.retro_trips)
		# summarize itinerary data
		self.sched_itins = self.summarize_itineraries(self.sched_trips)
		self.retro_itins = self.summarize_itineraries(self.retro_trips)
		# print summary info, including entropy
		print(self)

	def __repr__(self):
		name = self.orig['nomen']+' -> '+self.dest['nomen']
		entropy = '\n\tentropy-s:{},r:{}'.format(
			round(self.entropy(self.sched_itins),2),
			round(self.entropy(self.retro_itins),2)
		)
		sched = '\n\tsched | En:{e} Pr:{p}, It:{i}'.format(
			i=self.sched_itins[0]['itin'], 
			p=round(self.sched_itins[0]['prob'],3),
			e=round(self.entropy(self.sched_itins),2)
		)
		retro = '\n\tretro | En:{e} Pr:{p}, It:{i}'.format(
			i=self.retro_itins[0]['itin'], 
			p=round(self.retro_itins[0]['prob'],3),
			e=round(self.entropy(self.retro_itins),2)
		)
		return( name + sched + retro )

	def allocate_time(self,trips):
		"""Allocate the time for which this trip is the next fastest, clippng to 
		the window used for removing trips."""
		for trip in trips:
			return trip.depart
			

	def entropy(self,itineraries):
		"""shannon entropy of the itinerary probability distribution"""
		entropy = 0
		for itin in itineraries:
			entropy += itin['prob'] * log(itin['prob'],2)
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
				if trip.local_time('dep') > end or trip.local_time('arr') < start:
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
		# get distinct itineraries
		itins = set([trip.itin_uid for trip in trips])
		# put this in a dict with initial counts
		itins = { key:{'itin':key,'time':0,'count':0} for key in itins }
		# add times from trips to each 
		for i, trip in enumerate(trips):
			if i == 0: 
				from_prev = 60
			else:
				from_prev = trip.depart - trips[i-1].depart
			itins[trip.itin_uid]['time'] += from_prev
			itins[trip.itin_uid]['count'] += 1
		# change format from dict to list of dicts
		itins = [ itins[i] for i in itins ]
		# assign probabilities based on share of total time
		total_time = sum( [ i['time'] for i in itins ] )
		for i in itins: i['prob'] = i['time'] / total_time
		# and sort by prob, highest first
		itins = sorted(itins, key=lambda k: k['prob'],reverse=True) 
		return itins


