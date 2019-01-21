from OD import OD
import csv


def access(origin):
	"""origin-level access score - of some kind TBD"""
	# get a list of all OD IDs from file
	with open('data/ODs.csv') as f:
		reader = csv.DictReader(f)
		dests = [ int(r['uid']) for r in reader if int(r['uid']) != origin ]
	
	with open('data/test-access.csv','w+') as outfile:
		outfile.write('o,d,access')
		for dest in dests:
			print(dest)
			od = OD(origin,dest)
			a = od.access('h')
			outfile.write('\n'+str(origin)+','+str(dest)+','+str(a))


# simple function call to start with 
access(12)
