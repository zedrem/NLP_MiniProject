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

pages = db.pages
articles = db.articles

count = 0

for page in pages.find():
	body = page['body']
	id = page['_id']
	url = page['url']
	
	try:
		soup = BeautifulSoup(body)
		
		# Meta indicators - specific to Joel on software
		title = soup.find('h2').getText()
		author = soup.find('div', {"class": "author"}).getText()
		date = soup.find('div', {"class": "date"}).getText()
		

		
		if author.startswith('by '):
			author = author[3:]
		
		split_date = date.split(' ')
		dow = split_date[0][:-1]
		month = split_date[1]
		day = split_date[2][:-1]
		year = split_date[3]
		
		
		#print(title.encode())
		#print(author.encode())
		#print(date.encode())
		#print(dow.encode())
		#print(month.encode())
		#print(day.encode())
		#print(year.encode())
		#print("#")
		
		json_article = {
			"title": title,
			"author": author,
			"date": date,
			"dow": dow,
			"day": day,
			"month": month,
			"year": year,
			"body": body,
			"page": id,
			"url": url
		}
		
		articles.insert_one(json_article)
		
		count = count + 1
	
	except:
		print("Error")

print(count)
	
