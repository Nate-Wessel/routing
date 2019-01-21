from OD import OD
import csv


def access(origin):
	"""origin-level access score - of some kind TBD"""
	# get a list of all OD IDs from file
	with open('data/ODs.csv') as f:
		reader = csv.DictReader(f)
		dests = [ int(r['uid']) for r in reader if int(r['uid']) != origin ]
	
	with open('data/test-access.csv','w+',buffering=1) as outfile:
		outfile.write('o,d,ah,aa,plaus_itins,entropy')
		for dest in dests:
			print(dest)
			od = OD(origin,dest)
			Ah = od.access('habitual')
			Aa = od.access('any_plausible')
			outfile.write('\n{},{},{},{},{},{}'.format(
				origin,dest,
				Ah,Aa,
				len(od.alter_itins),
				od.retro_entropy
			) )

# simple function call to start with 
access(12)
