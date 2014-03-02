#
#   LOUISREVIEWS MAIN MODULE LOADER
#

import configparser
import logging
import os


# load config information from module directory
# =============================================
config = configparser.ConfigParser()
config.read(os.path.join(__path__[0], 'srtools.ini'))

# paths
# -----
cochrane_reviews_path = config["Paths"]["COCHRANE_REVIEWS_PATH"]
pubmed_abstracts_path = config["Paths"]["PUBMED_ABSTRACTS_PATH"]
pdfs_path = config["Paths"]["PDFS_PATH"]

# logging
# -------

logfile = os.path.join(__path__[0], config["Logging"]["LOG_FILE"])

if config.getboolean("Logging", "CLEAR_LOG_ON_RUN"):
	with open(logfile, 'w'): 
	    pass

if config.getboolean("Logging", "DEBUG_MODE"):
	logging.basicConfig(filename=logfile, level=logging.DEBUG)
else:
	logging.basicConfig(filename=logfile, level=logging.INFO)
