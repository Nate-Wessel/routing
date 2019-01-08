# This is for getting detailed stats on a single OD, mainly for diagnostic tests
from OD import OD
import csv, db

# get a list of all ODs from file
all_locations = {}
with open('ODs.csv') as f:
	reader = csv.DictReader(f)
	for r in reader:
		all_locations[r['uid']] = dict(r)

# these need to be specified as strings
o = '12'
d = '316'
od = OD(all_locations[o], all_locations[d] )

# get the departures and arrivals for the top three trips
# and put them in a CSV

with open('test.csv','w') as outfile:
	outfile.write('depart,arrive,itinerary\n')
	for i in [0,1,2]:
		for depart,arrive in db.all_itinerary_trips(od.retro_itin(i)):
			outfile.write(str(depart)+','+str(arrive)+','+str(od.retro_itin(i))+'\n')

#for trip in od.retro_trips:
#	trip.verify()
