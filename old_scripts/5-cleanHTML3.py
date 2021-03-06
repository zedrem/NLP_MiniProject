import json
import os
import sys
from pymongo import MongoClient
import urllib3
from bs4 import BeautifulSoup, SoupStrainer

# Get Config file
with open("config.json") as config_file:
    config = json.load(config_file)

# Connect to mongo
client = MongoClient("mongodb://" + os.environ['IP'] + "/") #for cloud nine, use MongoClient(config['db_url']) for config
db = client[config['db_client']]

articles = db.articles

count = 0

for article in articles.find():
	body = article['body']
	id = article['_id']
	
	#try:
	soup = BeautifulSoup(body)
	
	from_pos = soup.find('div', {"class": "date"})
	to_pos = soup.find('br', {"clear":"all"})

	text = ""
	
	for tag in from_pos.next_siblings:
		if tag == to_pos:
			break
		else:
			try:
				text += tag.text
			except: 
				pass
			
	#print("#")
	#print(from_pos)
	#print(to_pos)
	#print(text.encode())
	#print("#")
		
	articles.update({"_id": id }, {"$set": {
			"article_text": text,
		}})	
		
		
	count = count + 1
	
	#except:
	#	print("Error")

print(count)
	
