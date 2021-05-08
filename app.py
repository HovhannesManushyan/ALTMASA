from flask import Flask, render_template
import os
from flask import request
from flask import send_from_directory
from werkzeug.utils import secure_filename

import pdfplumber
import string
from nltk.tokenize import RegexpTokenizer
from gensim import corpora
from gensim import similarities
from gensim.models import TfidfModel
import pyLDAvis.gensim_models


data_collection = []

pdfs=os.listdir("static/literature")

for i in pdfs:
    with open(f"text/{i[:-4]}.txt","r",encoding="utf-8") as f: 
        data_collection.append(f.read())

punct = "։֊«»ՙ՚՛՜՝՞,:`"+string.punctuation
tokenizer = RegexpTokenizer(r'\w+')
def process(sentence):
    sentence=sentence.translate(str.maketrans('', '', punct))
    sentence=sentence.translate(str.maketrans('', '', string.digits))
    sentence=tokenizer.tokenize(sentence.lower())
    sentence=[i for i in sentence if len(i)>4]
    return sentence

data_collection=[process(i) for i in data_collection]
dictionary = corpora.Dictionary(data_collection)
corpus = [dictionary.doc2bow(text) for text in data_collection]
tfidf = TfidfModel(corpus)

app = Flask(__name__,static_folder=os.path.abspath("static/"))

@app.after_request
def add_header(r):
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    r.headers['Cache-Control'] = 'public, max-age=0'
    return r

@app.route("/")
def handle_index():
    if "message" in request.args:
        tfvec=tfidf[dictionary.doc2bow(process(request.args["message"]))]
        index = similarities.MatrixSimilarity(tfidf[corpus])
        sims = index[tfvec]
        sims = sorted(enumerate(sims), key=lambda item: -item[1])
        print(sims)
        if sims[0][1]>0.1:
            return send_from_directory("static/literature", pdfs[sims[0][0]])
        else:
            print(sims)
            return send_from_directory("static", "notenough.html")
    elif "messagenc" in request.args:
        tfvec=tfidf[dictionary.doc2bow(process(request.args["messagenc"]))]
        index = similarities.MatrixSimilarity(tfidf[corpus])
        sims = index[tfvec]
        sims = sorted(enumerate(sims), key=lambda item: -item[1])
        return send_from_directory("static/literature", pdfs[sims[0][0]])
    else:
        return render_template('index.html')

@app.route("/upload.html", methods=['POST','GET'])
def handle_upload():
    if request.method == "POST":
        tfile=request.files.get("fcont")
        filename = secure_filename(tfile.filename)
        tfile.save(os.path.join("saved_files/", filename))
        with pdfplumber.open(f"saved_files/{filename}") as pdf:
            data="\n".join([i.extract_text() for i in pdf.pages])
        clean_data=[process(i) for i in data.split(":")]
        dictionary=corpora.Dictionary(clean_data)
        corpus  = [dictionary.doc2bow(i) for i in clean_data]
        model2=LdaModel(corpus, num_topics=10, id2word = dictionary)
        p=pyLDAvis.gensim_models.prepare(model2, corpus,dictionary)
        pyLDAvis.save_html(p, 'static/lda.html')
        return send_from_directory("static", f"lda.html")
    else:
        return render_template('upload.html')



if __name__ == "__main__":
    app.run()