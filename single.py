# This is for getting detailed stats on a single OD, mainly for diagnostic tests
from OD import OD
import db

oid = 12
did = 316
od = OD(oid,did)

print( od )
print( od.access('habitual') )
print( od.access('any') )

# get the departures and arrivals for the top three trips
# and put them in a CSV

#with open('data/test.csv','w') as outfile:
#	outfile.write('depart,arrive,itinerary\n')
#	for i in [0,1,2]:
#		if od.retro_itin(i):
#			for trip in db.all_itinerary_trips(od.retro_itin(i)):
#				outfile.write(str(trip.depart_ts)+','+str(trip.arrive_ts)+',"'+str(od.retro_itin(i))+'"\n')

#for trip in od.retro_trips:
#	trip.verify()
