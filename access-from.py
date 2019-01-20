from OD import OD
import csv


def access(origin):
	"""origin-level access score - of some kind TBD"""
	# get a list of all OD IDs from file
	with open('data/ODs.csv') as f:
		reader = csv.DictReader(f)
		dests = [ int(r['uid']) for r in reader if int(r['uid']) != origin ]
	
	ODs = []
	for dest in dests:
		print(dest)
		od = OD(origin,dest)
		print( len(od.access()),'trips' )
		ODs.append( od )


# simple function call to start with 
access(12)
