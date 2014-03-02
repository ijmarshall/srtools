#
#	linker.py
#

"""
Tries multiple searches using different parts of the reference each time
Then iterates through all possible combinations of result sets, intersections are likely matches
Choose the id with the most hits (which appears most frequently as a single intersection).
"""

# standard srtools import
# =======================
import srtools
logger = srtools.logging.getLogger(__name__) # use logging defaults from srtools ini file
logger.info("test log from pubmedlinker.py")



import Queue
import collections
from glob import glob
import itertools
import json
import logging
from pprint import pprint
import sys
import threading
import traceback

import louisreviews
from pmlib import *
from readers.rm5lib_beta import *






class rm5toPubmed:
	def __init__(self, ref = None):
		
		self.pubmed_connection = pubmed()
		self.queue = Queue.Queue()
		self.ids = collections.deque()
		
		# make new thread instances
		for i in range(5):
			t = GetSearchesWorker(self.queue, self.ids)
			t.setDaemon(True)
			t.start()
	
	
	def update_ref(self, ref):

		if len(ref["TI"]) > 0:
			# this stage is needed since the title is the only unique search conducted
			# others rely on multiple points of data so more resilient
			self.searches = [ref["TI"], # title only - not tagged full text search
				'%s[firstauthor]' % (ref["fAU"], ), # first author
				'%s[journal] %s[pagination]' % (ref["SO"], ref["fPG"]), # journal and first page number
				'%s[volume] %s[date - publication] %s[pagination]' % (ref["VL"], ref["YR"], ref["fPG"]), # volume, year, and first page number
				'[author] '.join(ref["AU"] + [""]), # list of all authors
				'%s[journal] %s[volume] %s[issue]' % (ref["SO"], ref["VL"], ref["NO"]) # journal, volume, and issue
				]	
		else:
			self.searches = ['%s[firstauthor]' % (ref["fAU"], ), # first author
				'%s[journal] %s[pagination]' % (ref["SO"], ref["fPG"]), # journal and first page number
				'%s[volume] %s[date - publication] %s[pagination]' % (ref["VL"], ref["YR"], ref["fPG"]), # volume, year, and first page number
				'[author] '.join(ref["AU"] + [""]), # list of all authors
				'%s[journal] %s[volume] %s[issue]' % (ref["SO"], ref["VL"], ref["NO"]) # journal, volume, and issue
				]
	
	
	def link(self):
		search_results = self._get_searches()
		# pprint(search_results)
		decision = collections.Counter()		
		
		for combo in itertools.combinations(search_results, 2):
			intersect = combo[0].intersection(combo[1])
			#if len(intersect) == 1:
			decision.update(intersect)
		
		if len(decision) == 0:
			pmid, intersections = None, None
		else:
			pmid, intersections = decision.most_common(1)[0]  # retrieves the 1 most common, but as list of length one
			
		return pmid, intersections
		
	def spinner(self):
		"""
		simple spinner shows ongoing search progress
		"""
		sys.stdout.write(".")
		sys.stdout.flush()
		
	def clear_spinner(self):
		sys.stdout.write("       \b\b\b\b\b\b\b")
	
	def _get_searches(self):
		
		self.ids.clear()
		self.clear_spinner()
		
				
		for search in self.searches:
			self.queue.put(search)
			
		self.queue.join()

		return self.ids



class GetSearchesWorker(threading.Thread):
	def __init__(self, queue, ids):
		threading.Thread.__init__(self)
		self.queue = queue
		self.ids = ids
		self.pubmed_connection = pubmed()
		
	def run(self):
		while True:
			search = self.queue.get()
			sys.stdout.write(".")
			sys.stdout.flush()
			result = self.pubmed_connection.esearch(search)
			id_set = result["IdList"]
			self.ids.append(id_set)
			sys.stdout.write("\b \b")
			sys.stdout.flush()
			self.queue.task_done()


class LookupMaker():
	"""
	Generates a lookup dict relating CDSR references to pubmed IDs
	Saves as a JSON file
	"""
	def __init__(self, cdsr_files, output_file):
		self.lookup = self.attempt_load_json(output_file)
		self.cdsr_files = cdsr_files
		self.output_file = output_file
	
	def _cdno_from_file(self, filename):
		"""
		All the revman files used have the CD no in the filename
		This does not get the proper number from the XML
		"""
		return re.search('(?:CD|MR)[0-9]+', filename).group(0)
	
	def attempt_load_json(self, output_file):
		"""
		Try to load the data file, if not available start afresh
		"""
		try:
			with open(output_file, 'rb') as f:
				return json.load(f)
		except:
			return {}

	def save_json(self, data, output_file):
		"""
		Save the data in memory as a JSON file
		"""
		with open(output_file, 'wb') as f:
			json.dump(data, f)
			
	def progress(self, cdno, refno_current, refno_total, revno_current, revno_total):
		"""
		Simple progress bar
		"""
		if refno_total > 0:
			percentage_progress = (100 * refno_current) / (refno_total)
		else:
			percentage_progress = 100
			
		no_bars = percentage_progress / 5
		no_spaces = 20 - no_bars
		
		
		sys.stdout.write("\r%s [%s%s] %d%% (review %d of %d, %d/%d refs) " % (cdno, "=" * no_bars, " " * no_spaces, percentage_progress, revno_current, revno_total, refno_current, refno_total))
		sys.stdout.flush()
		
		
	def fetch_data(self, save_point=10): # save_point=number of reviews to save
		"""
		Main loop for generating index
		"""
		files_completed = set(self.lookup.keys())
		files_todo = set(self.cdsr_files).difference(files_completed)
	
		revno_in_cdsr = len(self.cdsr_files)
		revno_total = len(files_todo)
		revno_done = len(files_completed)
	
		linker = rm5toPubmed()
	
		for revno_current, cdsr_file in enumerate(files_todo):
				
			review = rm5(cdsr_file)
			self.lookup[cdsr_file]={}
			
			
			self.progress(self._cdno_from_file(cdsr_file), 0, 100, revno_current + revno_done + 1, revno_in_cdsr)
			
			refs = review.refs(full_parse=True)
			#with open('dump.txt', 'wb') as dump:
			#	pprint(refs, dump)	
		
			refno_total = len(refs)
			
			for refno_current, ref in enumerate(refs):
				self.progress(self._cdno_from_file(cdsr_file), refno_current, refno_total, revno_current + revno_done + 1, revno_in_cdsr)
					# 1 added to revno_current since 0 indexed (want to first display review 1) 
					# same *not* done to refno_current as displayed as percentage (want to first display 0%)
					
				linker.update_ref(ref)
				result = linker.link()
				
				self.lookup[cdsr_file][ref["ID"]] = result
			
			self.progress(self._cdno_from_file(cdsr_file), refno_total, refno_total, revno_current + revno_done + 1, revno_in_cdsr)
			
				
			if revno_current % save_point == 0:
				self.save_json(self.lookup, self.output_file)
				print " saved"					
			else:
				print
		
		self.save_json(self.lookup, self.output_file)
	




def make_link_file(output_filename="reflinkage.json", save_point=5):
	"""
	makes a new JSON file in the format
	{CDSRfilename_n: {CDSRrefid_1: PMID_1,
					  CDSRrefid_2: PMID_2,
					  CDSRrefid_n: PMID_n},
	...

	"""
	input_path = louisreviews.PATH["COCHRANE"]
	cdsr_files = glob('%s*.rm5' % (input_path, ))
	
	l = LookupMaker(cdsr_files, louisreviews.PATH["DATA"] + output_filename)	
	
	try:
		l.fetch_data(save_point)
		print
		print "finished!"
		
	except KeyboardInterrupt:
		print
		print 'Exiting'
		quit()
	except:
		print
		print 'Error - writing traceback and variables to file'
		with open('errlog.txt', 'a') as debug_file:
			pprint("TRACEBACK", debug_file)
			traceback.print_exc(debug_file)
			pprint("VARIABLES", debug_file)
			pprint(locals(), debug_file)
			
		quit()
	
def main():
	make_link_file("reflinkage-2013-10-10b.json")

if __name__ == '__main__':
	main()
		