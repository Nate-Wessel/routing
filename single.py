# This is for getting detailed stats on a single OD, mainly for diagnostic tests
from OD import OD
import db

oid = 316
did = 12
od = OD(oid,did)

# get the departures and arrivals for the top three trips
# and put them in a CSV

with open('data/test.csv','w') as outfile:
	outfile.write('depart,arrive,itinerary\n')
	for i in [0,1,2]:
		for depart,arrive in db.all_itinerary_trips(od.retro_itin(i)):
			outfile.write(str(depart)+','+str(arrive)+',"'+str(od.retro_itin(i))+'"\n')

#for trip in od.retro_trips:
#	trip.verify()
