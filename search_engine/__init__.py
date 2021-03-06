from flask import Flask
from flask.ext.mongoengine import MongoEngine
from flask import flash, redirect, url_for, request, render_template
import json
import os
import nltk
import string
from pymongo import MongoClient
from nltk.corpus import wordnet
import time

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
    
    
# @app.route('/users/', defaults={'page': 1})
# @app.route('/users/page/<int:page>')

# @app.route('/search/', defaults={"page": 1}, methods=['POST'])
# @app.route('/search/page/<int:page>', methods=['POST'])


@app.route('/search/', defaults={"page": 1}, methods=['GET','POST'])
# @app.route('/search/page/<int:page>/<scope>/<ne>/<ee>/<query>', methods=['GET','POST'])
@app.route('/search/page/<int:page>', methods=['GET','POST'])

def search(page):
    t0 = time.time()
    results_list = []
    article_list = []
    # q = ""
    
    try:
        scope = request.args.get('scope')
        namedEnts = request.args.get('ne')
        eventEnts = request.args.get('ee')
        q = request.args.get('query')
        # scope = kwargs.get('scope', None)
        # namedEnts = kwargs.get('ne', None)
        # eventEnts = kwargs.get('ee', None)
        # q = kwargs.get('query', None)
    except:
        pass
    
    if not q and not scope:
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
            res = db.paragraph_final_word_list.find()
        elif scope == "sentence":
            res = db.sentence_final_word_list.find()
        else:
            res = db.final_word_list.find()
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
                                        rank = db.paragraph_ranked_results.find_one({"url": url[0], "paragraph_number":url[1]})
                                        results_list += [[rank['score'], [url]]]
                            
                    elif scope == "sentence":
                        res = db.sentence_final_word_list.find_one({"word":word})
                        
                        if res:
                            urls = res['urls']
                            
                            for url in urls:
                                event_exists = db.sentence_event_entities.find_one({"url": url[0], "paragraph_number": url[1], "sentence_number": url[2]})
                                if event_exists:
                                    if url not in results_list:
                                        rank = db.sentence_ranked_results.find_one({"url": url[0], "paragraph_number":url[1], "sentence_number": url[2]})
                                        results_list += [[rank['score'], [url]]]
                    else:
                        res = db.final_word_list.find_one({"word": word})
                        if res:
                            urls = res['urls']
                        
                            for url in urls:
                                event_exists = db.event_entities.find_one({"url": url})
                                if event_exists:
                                    if url not in results_list:
                                        rank = db.ranked_results.find_one({"url": url})
                                        results_list += [[rank['score'], [url]]]
                    
                    syns = wordnet.synsets(word)
                    r = []
                    for syn in syns:
                        for l in syn.lemmas():
                            if scope == "paragraph":
                                res = db.paragraph_final_word_list.find_one({"word": l.name()})
                            elif scope == "sentence":
                                res = db.sentence_final_word_list.find_one({"word": l.name()})
                            else:
                                res = db.final_word_list.find_one({"word": l.name()})
                            
                            if res:
                                for url in res['urls']:
                                    if scope == "paragraph":
                                        event_exists = db.paragraph_event_entities.find_one({"url":url})
                                    elif scope == "sentence":
                                        event_exists = db.sentence_event_entities.find_one({"url":url})
                                    else:
                                        event_exists = db.event_entities.find_one({"url":url})
                                    if event_exists:
                                        if url not in r:
                                            if scope == "paragraph":
                                                rank = db.paragraph_ranked_results.find_one({"url": url[0], "paragraph_number": url[1]})
                                            elif scope == "sentence":
                                                rank = db.sentence_ranked_results.find_one({"url": url[0], "paragraph_number": url[1], "sentence_number": url[2]})
                                            else:
                                                rank = db.ranked_results.find_one({"url": url})
                                                
                                            
                                            r += [[rank['score'], [url]]]
                    
                    # print r
                    # print results_list
                    for rs in r:
                        if rs not in results_list:
                            results_list += [rs]
                                   
                
                # event ents
                for word in filtered_sentence:
                    if scope == "paragraph":
                        res = db.paragraph_event_word_list.find_one({"word": word})
                        if res:
                            urls = res['urls']
                            
                            for url in urls:
                                if url not in results_list:
                                    rank = db.paragraph_ranked_results.find_one({"url": url[0], "paragraph_number":url[1]})
                                    results_list += [[rank['score'], [url]]]
                    elif scope == "sentence":
                        res = db.sentence_event_word_list.find_one({"word": word})
                        if res:
                            urls = res['urls']
                            
                            for url in urls:
                                if url not in results_list:
                                    rank = db.sentence_ranked_results.find_one({"url": url[0], "paragraph_number":url[1], "sentence_number": url[2]})
                                    results_list += [[rank['score'], [url]]]
                    else:
                        res = db.event_word_list.find_one({"word": word})
                        if res:
                            urls = res['urls']
                            
                            for url in urls:
                                if url not in results_list:
                                    rank = db.ranked_results.find_one({"url": url})
                                    results_list += [[rank['score'], [url]]]
                    
                    syns = wordnet.synsets(word)
                    r = []
                    for syn in syns:
                        for l in syn.lemmas():
                            if scope == "paragraph":
                                res = db.paragraph_event_word_list.find_one({"word": l.name()})
                            elif scope == "sentence":
                                res = db.sentence_event_word_list.find_one({"word": l.name()})
                            else:
                                res = db.event_word_list.find_one({"word": l.name()})
                            
                            if res:
                                for url in res['urls']:
                                    if url not in r:
                                        if scope == "paragraph":
                                            rank = db.paragraph_ranked_results.find_one({"url": url[0], "paragraph_number": url[1]})
                                        elif scope == "sentence":
                                            rank = db.sentence_ranked_results.find_one({"url": url[0], "paragraph_number": url[1], "sentence_number": url[2]})
                                        else:
                                            rank = db.ranked_results.find_one({"url": url})
                                            
                                        r += [[rank['score'], [url]]]
                    # print r
                    for rs in r:
                        if rs not in results_list:
                            results_list += [rs]
            else:
                for word in filtered_sentence:
                    if scope == "paragraph":
                        res = db.paragraph_final_word_list.find_one({"word": word})
                        if res:
                            urls = res['urls']
                        
                            for url in urls:
                                if url not in results_list:
                                    rank = db.paragraph_ranked_results.find_one({"url": url[0], "paragraph_number":url[1]})
                                    results_list += [[rank['score'], [url]]]
                    elif scope == "sentence":
                        res = db.sentence_final_word_list.find_one({"word": word})
                        if res:
                            urls = res['urls']
                        
                            for url in urls:
                                if url not in results_list:
                                    rank = db.sentence_ranked_results.find_one({"url": url[0], "paragraph_number":url[1], "sentence_number": url[2]})
                                    results_list += [[rank['score'], [url]]]
                    else:
                        res = db.final_word_list.find_one({"word": word})
                        if res:
                            urls = res['urls']
                        
                            for url in urls:
                                if url not in results_list:
                                    rank = db.ranked_results.find_one({"url": url})
                                    results_list += [[rank['score'], [url]]]
                    
                    syns = wordnet.synsets(word)
                    r = []
                    for syn in syns:
                        for l in syn.lemmas():
                            if scope == "paragraph":
                                res = db.paragraph_final_word_list.find_one({"word": l.name()})
                            elif scope == "sentence":
                                res = db.sentence_final_word_list.find_one({"word": l.name()})
                            else:
                                res = db.final_word_list.find_one({"word": l.name()})
                            
                            if res:
                                for url in res['urls']:
                                    if url not in r:
                                        if scope == "paragraph":
                                            rank = db.paragraph_ranked_results.find_one({"url": url[0], "paragraph_number": url[1]})
                                        elif scope == "sentence":
                                            rank = db.sentence_ranked_results.find_one({"url": url[0], "paragraph_number": url[1], "sentence_number": url[2]})
                                        else:
                                            rank = db.ranked_results.find_one({"url": url})
                                            
                                        r += [[rank['score'], [url]]]
                    # print r
                    for rs in r:
                        if rs not in results_list:
                            results_list += [rs]
        else:
            if eventEnts:
                for word in filtered_sentence:
                    if scope == "paragraph":
                        res = db.paragraph_event_word_list.find_one({"word": word})
                        if res:
                            urls = res['urls']
                            
                            for url in urls:
                                if url not in results_list:
                                    rank = db.paragraph_ranked_results.find_one({"url": url[0], "paragraph_number":url[1]})
                                    results_list += [[rank['score'], [url]]]
                    elif scope == "sentence":
                        res = db.sentence_event_word_list.find_one({"word": word})
                        if res:
                            urls = res['urls']
                            
                            for url in urls:
                                if url not in results_list:
                                    rank = db.sentence_ranked_results.find_one({"url": url[0], "paragraph_number":url[1], "sentence_number": url[2]})
                                    results_list += [[rank['score'], [url]]]
                    else:
                        res = db.event_word_list.find_one({"word": word})
                        if res:
                            urls = res['urls']
                            
                            for url in urls:
                                if url not in results_list:
                                    rank = db.ranked_results.find_one({"url": url})
                                    results_list += [[rank['score'], [url]]]
                    
                    syns = wordnet.synsets(word)
                    r = []
                    for syn in syns:
                        for l in syn.lemmas():
                            if scope == "paragraph":
                                res = db.paragraph_event_word_list.find_one({"word": l.name()})
                            elif scope == "sentence":
                                res = db.sentence_event_word_list.find_one({"word": l.name()})
                            else:
                                res = db.event_word_list.find_one({"word": l.name()})
                            
                            if res:
                                for url in res['urls']:
                                    if url not in r:
                                        if scope == "paragraph":
                                            rank = db.paragraph_ranked_results.find_one({"url": url[0], "paragraph_number": url[1]})
                                        elif scope == "sentence":
                                            rank = db.sentence_ranked_results.find_one({"url": url[0], "paragraph_number": url[1], "sentence_number": url[2]})
                                        else:
                                            rank = db.ranked_results.find_one({"url": url})
                                            
                                        r += [[rank['score'], [url]]]
                    # print r
                    for rs in r:
                        if rs not in results_list:
                            results_list += [rs]
                            
            else:
                flash("Select at least one checkbox.")
                return render_template('search.html', articles=article_list, query=q, ne=namedEnts, ee=eventEnts, article_count=len(article_list))
    
    #pagination_code
    num_of_results = len(results_list)
    page_size = config['page_size_limit']
    
    ranked_list = []
    ranked_list = sorted(results_list,key=lambda results_item: results_item[0], reverse=True)
    
    print ranked_list
    
    rlist = [ranked_list[i:i+page_size] for i in range(0, num_of_results, page_size)]
    
    # print results_list
    # print ranked_list
    # print rlist
    res = []
    for r in rlist[page - 1]:
        res += [r[1][0]]
    
    # print res
    # print len(res)
    num_of_pages = len(rlist)
    
    if page < 1:
        page = 1
    
    if page > num_of_pages:
        page = num_of_pages
    

    # print page, num_of_pages, num_of_results, page_size
    #end pagination
    
    
    
    
    # get article for each item
    for url in res:
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
            article = db.articles.find_one({"url": url[0]})
            analysis = db.analysis.find_one({"url": url[0]})
            ranking = db.sentence_ranked_results.find_one({"url": url[0], "paragraph_number": url[1], "sentence_number": url[2]})
            score = ranking['score']
            
            sent = {}
            sentences = article['sentences']
            for s in sentences:
                if s['paragraph_number'] == url[1] and s['sentence_number'] == url[2]:
                    sent = s
                    # print url[0], para['paragraph_number']
            
            sent_anal = {}
            sentence_analysis = analysis['sentence_analysis']
            for a in sentence_analysis:
                if a['paragraph_number'] == url[1] and a['sentence_number'] == url[2]:
                    sent_anal = a
                    #print url[0], para_anal['paragraph_number']
            
            article_list += [[article, analysis, score, sent, sent_anal]]
        else:
            article = db.articles.find_one({"url": url})
            analysis = db.analysis.find_one({"url": url})
            ranking = db.ranked_results.find_one({"url": url})
            score = 0
            if ranking:
                score = ranking['score']
            
            article_list += [[article, analysis, score]]
        
    for item in article_list:
        article = item[0]
        score = item[2]
        url = article['url']
        
        count = 1
        for a in article_list:
            if a[0]['url'] == url:
                count += 1
        # print("old score:" + str(score))
        score += (count * 10)
        item[2] = score
        # print("new score:" + str(item[2]))
    
    # return list
    article_list = sorted(article_list,key=lambda article_item: article_item[2], reverse=True)
    #     #pagination_code
    # num_of_results = len(article_list)
    # page_size = config['page_size_limit']
    
    # rlist = [article_list[i:i+page_size] for i in range(0, num_of_results, page_size)]
    # num_of_pages = len(rlist)
    
    # if page < 1:
    #     page = 1
    
    # if page > num_of_pages:
    #     page = num_of_pages
    

    # print page, num_of_pages, num_of_results, page_size
    # #end pagination
        
    if len(article_list) == 0: 
        flash("No results found.")
        
    # flash(q)
    #flash(article_list[0])
    #return redirect(url_for('search', articles=article_list))
    elapsed = time.time() - t0
    return render_template('search.html', articles=article_list, query=q, ne=namedEnts, ee=eventEnts, scope=scope, article_count=num_of_results, time=elapsed, total_pages=num_of_pages, page=page)

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
            pnum = int(pnum)
    
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
        article = db.articles.find_one({"_id" : ObjectId(art_id)}) #db.articles.findOne({"_id" : ObjectId("5732766271218d764faf53b6")})
        # print art_id, article
        url = article['url']
        analysis = db.analysis.find_one({"url": url})
        ranking = db.sentence_ranked_results.find_one({"url": url, "paragraph_number": pnum, "sentence_number": snum})
        score = ranking['score']
        
        sent = {}
        sentences = article['sentences']
        for s in sentences:
            if s['paragraph_number'] == pnum and s['sentence_number'] == snum:
                sent = s
                
        
        sent_anal = {}
        sentence_analysis = analysis['sentence_analysis']
        for a in sentence_analysis:
            if a['paragraph_number'] == pnum and a['sentence_number'] == snum:
                sent_anal = a
        
        ne = db.sentence_named_entities.find_one({"url": url, "paragraph_number": pnum, "sentence_number": snum})
        ee = db.sentence_event_entities.find_one({"url": url, "paragraph_number": pnum, "sentence_number": snum})
        
        article = [article, analysis, score, sent, sent_anal, ne, ee]
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


@app.route('/nevisual', methods=['GET'])

def nevisual():
    nltk = db.word_list.find({}, {"word":1, "_id":0})
    stanford = db.stanford_word_list.find({}, {"word":1, "_id":0})
    noun = db.noun_word_list.find({}, {"word":1, "_id":0})
        
    nltk_list = []
    stan_list = []
    noun_list = []
    
    for n in nltk:
        nltk_list += [n['word']]
    
    for s in stanford:
        stan_list += [s['word']]
    
    for n in noun:
        noun_list += [n['word']]
        

    nltk_stanford = list(set(nltk_list) & set(stan_list))
    nltk_noun = list(set(nltk_list) & set(noun_list))
    stanford_noun = list(set(stan_list) & set(noun_list))
    nltk_stanford_noun = list(set(nltk_list) & set(stan_list) & set(noun_list))
    
    nltk_size = len(nltk_list)
    stan_size = len(stan_list)
    noun_size = len(noun_list)
    
    # print nltk_list
    # print nltk_stanford
    
    nl_st_size = len(nltk_stanford) 
    nl_no_size = len(nltk_noun) 
    st_no_size = len(stanford_noun)
    nl_st_no_size = len(nltk_stanford_noun) 
    
    values = [nltk_size, stan_size, noun_size, nl_st_size, nl_no_size, st_no_size, nl_st_no_size]
    
    #print values
    
    #  [{sets: ['NLTK'], size: 12},
    # {sets: ['Stanford'], size: 12},
    # {sets: ['Noun'], size: 12},
    # {sets: ['NLTK','Stanford'], size: 2},
    # {sets: ['NLTK', 'Noun'], size: 2},
    # {sets: ['Stanford', 'Noun'], size: 2},
    # {sets: ['NLTK', 'Stanford', 'Noun'], size: 2}]
    
    
    
    return render_template('ne_venn.html', values=values)