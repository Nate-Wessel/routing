# This is for getting detailed stats on a single OD, mainly for diagnostic tests
from OD import OD
import db

oid = 222
did = 208
od = OD(oid,did)

print( od )
print( 'realtime access:', od.access('realtime') )
print( 'habitual-access:', od.access('habitual') )
print( 'any access:', od.access('any') )

# get the departures and arrivals for the top three trips
# and put them in a CSV

# write all trips for the top itineraries to a file
with open('data/db-trips.csv','w') as outfile:
	outfile.write('depart,arrive,itinerary\n')
	for itin in od.alter_itins():
		for trip in itin.get_trips():
			outfile.write(str(trip.depart_ts)+','+str(trip.arrive_ts)+',"'+str(itin)+'"\n')

#for trip in od.retro_trips:
#	trip.verify()
