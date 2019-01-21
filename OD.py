from trip import Trip
import os, csv, time
from datetime import datetime, timedelta
from math import log
import config, db, impedance
from misc import *
from itinerary import Itinerary
from statistics import mean

class OD(object):
	"""An O->D pair"""
	def __init__(self,origin,dest):
		"""origin and dest are integer IDs"""
		self.orig = origin
		self.dest = dest
		# read in the trip itineraries
		self.retro_trips = self.get_trips_from_file('retro')
		self.sched_trips = self.get_trips_from_file('sched')
		self.allocate_time(self.sched_trips)
		self.allocate_time(self.retro_trips)
		# summarize itinerary data
		self.sched_itins = summarize_itineraries(self.sched_trips)
		self.retro_itins = summarize_itineraries(self.retro_trips)

	def __repr__(self):
		name = str(self.orig)+' -> '+str(self.dest)
		sched = '\n\tsched | entropy:{} | trips:{}'.format( 
			round(self.sched_entropy,2), len(self.sched_trips) )
		retro = '\n\tretro | entropy:{} | trips:{}'.format( 
			round(self.retro_entropy,2), len(self.retro_trips) )
		for i in [0,1,2]:
			sched += '\n\t\tPr:{}, '.format( round(self.sched_itin_p(i),3) )
			retro += '\n\t\tPr:{}, '.format( round(self.retro_itin_p(i),3) )
			sched += 'It:{}'.format( self.sched_itin(i) )
			retro += 'It:{}'.format( self.retro_itin(i) ) 
		return( name + sched + retro )

	@property
	def alter_itins(self):
		"""Return a list of itineraries where each is optimal at least 5% of the 
		time."""
		return [ itin for itin in self.retro_itins if itin.prob >= 0.05 ]

	def allocate_time(self,trips):
		"""Allocate the time (in seconds) for which this trip is the next, 
		clipping to the window used for removing trips."""
		# sort the trips by departure
		trips = sorted(trips, key=lambda k: k.depart) 
		dates_seen = set()
		for i, trip in enumerate(trips):
			if i == 0 or not trip.depart.date() in dates_seen:
				# trip is first of the day
				dates_seen |= {trip.depart.date()}
				# create a localized datetime 
				start_dt = config.tz.localize( datetime.combine(
					trip.depart.date(), config.window_start_time
				) )
				from_prev = (trip.depart - start_dt).total_seconds()
			else:
				# trip follows previous trip on this day 
				from_prev = (trip.depart - trips[i-1].depart).total_seconds()
			trip.time_before = from_prev
				
	def entropy(self,itineraries):
		"""shannon entropy of the itinerary probability distribution"""
		entropy = 0
		for itin in itineraries:
			entropy += itin.prob * log(itin.prob,2)
		return - entropy

	def get_trips_from_file(self,dataset):
		"""Check files for trips data and read it into a list. Remove any trips
		outside the time window as well as any suboptimal trips."""
		# directories to check
		if dataset == 'sched': 
			directories = ['sched'] 
		elif dataset == 'retro': 
			directories = ['17476','17477','17478','17479','17480']
		trips = []
		for d in directories:
			csvpath = config.input_dir+d+'/'+str(self.orig)+'/'+str(self.dest)+'.csv'
			if not os.path.exists(csvpath): continue			
			with open(csvpath) as f:
				reader = csv.DictReader(f)	
				trips.extend( 
					[ Trip(r['depart'],r['arrive'],r['itinerary']) for r in reader ]
				)
		# we now have all the data from the files but need to clean it
		clip_trips_to_window(trips)
		remove_premature_departures(trips)
		return trips

	def access(self,kind='habitual'):
		"""Return an average access score based on the given accessibility 
		metric"""
		if kind in ['habitual','h','H']:
			# route choice is based on whatever is generally the best from 
			# experience with no deviation from that route
			learned_itin = self.retro_itin(0)
			if learned_itin.is_walking:
				print('walking time used')
				# don't look up a walking trip - we already know the travel time
				seconds_walking = learned_itin.walk_distance / config.walk_speed
				walk_time = timedelta(seconds=seconds_walking)
				return impedance.negexp( walk_time )
			else:
				# this trip involves transit and we need to look up trips in the DB
				trips = db.all_itinerary_trips(learned_itin)
				clip_trips_to_window(trips)
				times = trips2times(trips)
				print(len(times),'times used')
				return mean( [ impedance.negexp(time) for time in times ] )
		elif kind in ['any_plausible','any','a']:
			# any route getting optimality 5%+ of the time can be used optimally
			all_possible_trips = []
			for plausible_itin in self.alter_itins:
				if plausible_itin.is_walking:
					print('walking time used')
					# don't look up a walking trip - we already know the travel time
					seconds_walking = plausible_itin.walk_distance / config.walk_speed
					walk_time = timedelta(seconds=seconds_walking)
					return impedance.negexp( walk_time )
				trips = db.all_itinerary_trips(plausible_itin)
				all_possible_trips.extend(trips)
			clip_trips_to_window(all_possible_trips)
			times = trips2times(all_possible_trips)
			print(len(times),'times used')
			return mean( [ impedance.negexp(time) for time in times ] )
		else: 
			print('invalid access type supplied')
			assert False

	# here be some simplifying properties/methods
	
	@property
	def sched_entropy(self):
		"""schedule-based entropy"""
		return self.entropy(self.sched_itins)
	@property
	def retro_entropy(self):
		"""retro-spective entropy"""
		return self.entropy(self.retro_itins)

	def sched_itin(self,i):
		"""scheduled itinerary at the given index if any"""
		return self.sched_itins[i] if i < len(self.sched_itins) else None
	def retro_itin(self,i):
		"""scheduled itinerary at the given index if any"""
		return self.retro_itins[i] if i < len(self.retro_itins) else None

	def sched_itin_p(self,i):
		"""scheduled itinerary probability at the given index if any"""
		return self.sched_itins[i].prob if i < len(self.sched_itins) else 0
	def retro_itin_p(self,i):
		"""scheduled itinerary probability at the given index if any"""
		return self.retro_itins[i].prob if i < len(self.retro_itins) else 0
	

