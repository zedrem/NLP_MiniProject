import os
import json
from pymongo import MongoClient

# Get Config file
with open("config.json") as config_file:
    config = json.load(config_file)

# Connect to mongo
client = MongoClient("mongodb://" + os.environ['IP'] + "/") #for cloud nine, use MongoClient(config['db_url']) for config
db = client[config['db_client']]

# Drop current indicators collection
indicators = db.indicators
indicators.drop()

# Add list of indicators from config file
indicators_list = config['indicators']

count = 0

for indicator in indicators_list:
	try:

		json_indicator = {
			"name": indicator
		}
		indicators.insert_one(json_indicator)
		
		count = count + 1
	
	except:
		print("Error")

print(count)
	
