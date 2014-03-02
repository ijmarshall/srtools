#
# flipLookup.py
#
#	convert output.json created by linker into more useful configuration
#	and save as pickle

"""
opens output.json
saves all confident links (those with 2 or more intersections on the search)
in a new json
"""

from glob import glob
import json
from pprint import pprint
import collections
from progressbar import *
import cPickle as pickle
from os.path import basename

def pmid_to_filename(pmid):
	return "%s.xml" % (pmid, )


def main():
	
	input_path = "/Users/iain/Code/data/cdsr2013/"
	cdsr_files = glob('%s*.rm5' % (input_path, ))
	
	with open('reflinkage-2013-10-10.json', 'rb') as f:
		lookup = json.load(f)	
	
	
	
	
	# make list of where more than one intersection
	converted_lookup = []
	
	pb = ProgressBar(len(lookup))
		
	for cdsr_filename, ref_dict in lookup.iteritems():
		
		pb.tap()
		

		cdsr_filename_nopath = basename(cdsr_filename)

		
		
		for cdsr_refcode, (pmid, no_intersections) in ref_dict.iteritems():
			
			if no_intersections > 2:
				converted_lookup.append({"cdsr_filename":cdsr_filename_nopath,
										 "cdsr_refcode":cdsr_refcode,
										 "pmid": pmid})
					
	
	
	with open('biviewer_lookup_c.pck', 'wb') as f:
		pickle.dump(converted_lookup, f)
		
	print "done!"
	


if __name__ == '__main__':
	main()