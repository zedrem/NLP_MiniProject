from flask import Flask
from flask.ext.mongoengine import MongoEngine
from flask import flash, redirect, url_for, request, render_template
import json
import os
import nltk
import string
from pymongo import MongoClient


app = Flask(__name__)

ip = os.environ['IP']
port = int(os.environ['PORT'])



# # connect to MongoDB server
# app.config['MONGODB_HOST'] = ip
# #app.config['MONGODB_PORT'] = port
# app.config['MONGODB_DBNAME'] = 'uc-proto'
# app.config['MONGO_CONNECT'] = True
app.config["SECRET_KEY"] = "KeepThisS3cr3t"

# mongo = PyMongo(app, config_prefix='MONGODB')
# mongo = MongoEngine(app)

# Get Config file
with open("../settings/config.json") as config_file:
    config = json.load(config_file)

# Connect to mongo
client = MongoClient("mongodb://" + os.environ['IP'] + "/") #for cloud nine, use MongoClient(config['db_url']) for config
db = client[config['db_client']]

if __name__ == '__main__':
    port = port
    host = ip
    app.run(port=port, host=host)
    
def register_blueprints(app):
    # Prevents circular imports
    from search_engine.views import search
    app.register_blueprint(search)

register_blueprints(app)

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')
    
@app.route('/search', methods=['POST'])

def search():
    results_list = []
    article_list = []
    
    q = request.form['query']
    # print request.values
    # ar = request.args
    checked = request.form.getlist("checked")
    scope = request.form.get("scope")
    
    # print radio
    
    if "namedEnts" in checked:
        namedEnts = True
    else:
        namedEnts = False
    
    if "eventEnts" in checked:
        eventEnts = True
    else:
        eventEnts = False
        
    # 
    #results = db.articles.count()
    #flash(str(config['seed']))
    #flash(str(results))
    q = q.lower()
    
    punctuation_exceptions = ['/']
    for c in string.punctuation:
        #try:
        if c in punctuation_exceptions:
            q = q.replace(c, " ")
        else:
            q = q.replace(c,"")
    
    
    #sent tokenise
    #sentences = nltk.sent_tokenise(q)
    #word tokenise
    words = nltk.word_tokenize(q)
    
    #stop_words = set(nltk.stopwords.words("english"))
    #filtered_sentence = []
    filtered_sentence = words
    
    # for w in words:
    #     if w not in stop_words:
    #         filtered_sentence.append(w)
            
    for w in filtered_sentence:
        w = w.lower()
        
        punctuation_exceptions = ['/']
        for c in string.punctuation:
            #try:
            if c in punctuation_exceptions:
                w = w.replace(c, " ")
            else:
                w = w.replace(c,"")
        
    if q == "all":
        if scope == "paragraph":
            res = db.paragraph_final_word_list.find().limit(50)
        elif scope == "sentence":
            res = db.sentence_final_word_list.find().limit(50)
        else:
            res = db.final_word_list.find().limit(50)
        for r in res:
            urls = r['urls']
            
            for url in urls:
                if url not in results_list:
                    results_list += [url]
        print len(results_list)
    else:
        if namedEnts:
            if eventEnts:
                # named_ents
                for word in filtered_sentence:
                    if scope == "paragraph":
                        res = db.paragraph_final_word_list.find_one({"word":word})
                        
                        if res:
                            urls = res['urls']
                            
                            for url in urls:
                                event_exists = db.paragraph_event_entities.find_one({"url": url[0], "paragraph_number": url[1]})
                                if event_exists:
                                    if url not in results_list:
                                        results_list += [url]
                            
                    elif scope == "sentence":
                        print "sentence"
                    else:
                        res = db.final_word_list.find_one({"word": word})
                        if res:
                            urls = res['urls']
                        
                            for url in urls:
                                event_exists = db.event_entities.find_one({"url": url})
                                if event_exists:
                                    if url not in results_list:
                                        results_list += [url]
                # event ents
                for word in filtered_sentence:
                    if scope == "paragraph":
                        res = db.paragraph_event_word_list.find_one({"word": word})
                        if res:
                            urls = res['urls']
                            
                            for url in urls:
                                if url not in results_list:
                                    results_list += [url]
                    elif scope == "sentence":
                        print "sentence"
                    else:
                        res = db.event_word_list.find_one({"word": word})
                        if res:
                            urls = res['urls']
                            
                            for url in urls:
                                if url not in results_list:
                                    results_list += [url]
            else:
                for word in filtered_sentence:
                    if scope == "paragraph":
                        res = db.paragraph_final_word_list.find_one({"word": word})
                        if res:
                            urls = res['urls']
                        
                            for url in urls:
                                if url not in results_list:
                                    results_list += [url]
                    elif scope == "sentence":
                        print "sentence"
                    else:
                        res = db.final_word_list.find_one({"word": word})
                        if res:
                            urls = res['urls']
                        
                            for url in urls:
                                if url not in results_list:
                                    results_list += [url]
        else:
            if eventEnts:
                for word in filtered_sentence:
                    if scope == "paragraph":
                        res = db.paragraph_event_word_list.find_one({"word": word})
                        if res:
                            urls = res['urls']
                            
                            for url in urls:
                                if url not in results_list:
                                    results_list += [url]
                    elif scope == "sentence":
                        print "sentence"
                    else:
                        res = db.event_word_list.find_one({"word": word})
                        if res:
                            urls = res['urls']
                            
                            for url in urls:
                                if url not in results_list:
                                    results_list += [url]
            else:
                flash("Select at least one checkbox.")
                return render_template('search.html', articles=article_list, query=q, ne=namedEnts, ee=eventEnts, article_count=len(article_list))
                            
    
    # get article for each item
    for url in results_list:
        if scope == "paragraph":
            article = db.articles.find_one({"url": url[0]})
            analysis = db.analysis.find_one({"url": url[0]})
            ranking = db.paragraph_ranked_results.find_one({"url": url[0], "paragraph_number": url[1]})
            score = ranking['score']
            
            para = {}
            paragraphs = article['paragraphs']
            for p in paragraphs:
                if p['paragraph_number'] == url[1]:
                    para = p
                    # print url[0], para['paragraph_number']
            
            para_anal = {}
            paragraph_analysis = analysis['paragraph_analysis']
            for a in paragraph_analysis:
                if a['paragraph_number'] == url[1]:
                    para_anal = a
                    #print url[0], para_anal['paragraph_number']
            
            article_list += [[article, analysis, score, para, para_anal]]
        elif scope == "sentence":
            print "sentence"
        else:
            article = db.articles.find_one({"url": url})
            analysis = db.analysis.find_one({"url": url})
            ranking = db.ranked_results.find_one({"url": url})
            score = ranking['score']
            
            article_list += [[article, analysis, score]]
        
    
    # return list
    article_list = sorted(article_list,key=lambda article_item: article_item[2], reverse=True)
        
    if len(article_list) == 0: 
        flash("No results found.")
        
    # flash(q)
    #flash(article_list[0])
    #return redirect(url_for('search', articles=article_list))
    return render_template('search.html', articles=article_list, query=q, ne=namedEnts, ee=eventEnts, scope=scope, article_count=len(article_list))

@app.route('/result/<art_id>/<pnum>/<snum>/<scope>/<ne>/<ee>/<query>', methods=['GET', 'POST'])

def result(art_id, pnum, snum, scope, ne, ee, query):
    from bson.objectid import ObjectId
    
    
    if pnum == 'x':
        scope = 'article'
    else:
        if snum == 'x':
            scope = 'paragraph'
            pnum = int(pnum)
        else:
            scope = 'sentence'
            snum = int(snum)
    
    article = []
    
    if scope == "paragraph":
        article = db.articles.find_one({"_id" : ObjectId(art_id)}) #db.articles.findOne({"_id" : ObjectId("5732766271218d764faf53b6")})
        # print art_id, article
        url = article['url']
        analysis = db.analysis.find_one({"url": url})
        ranking = db.paragraph_ranked_results.find_one({"url": url, "paragraph_number": pnum})
        score = ranking['score']
        
        para = {}
        paragraphs = article['paragraphs']
        for p in paragraphs:
            if p['paragraph_number'] == pnum:
                para = p
                
        
        para_anal = {}
        paragraph_analysis = analysis['paragraph_analysis']
        for a in paragraph_analysis:
            if a['paragraph_number'] == pnum:
                para_anal = a
        
        ne = db.paragraph_named_entities.find_one({"url": url, "paragraph_number": pnum})
        ee = db.paragraph_event_entities.find_one({"url": url, "paragraph_number": pnum})
        
        article = [article, analysis, score, para, para_anal, ne, ee]
    elif scope == "sentence":
        print "sentence"
    else:
        article = db.articles.find_one({"_id" : ObjectId(art_id)})
        url = article['url']
        analysis = db.analysis.find_one({"url": url})
        ranking = db.ranked_results.find_one({"url": url})
        score = ranking['score']
        
        ne = db.named_entities.find_one({"url": url})
        ee = db.event_entities.find_one({"url": url})
        
        
        article = [article, analysis, score, ne, ee]

    
    return render_template('result.html', article=article, scope=scope, ne=ne, ee=ee, query=query)
