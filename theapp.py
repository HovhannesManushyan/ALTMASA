from flask import Flask, render_template
import os
from flask import request
from flask import send_from_directory
from werkzeug.utils import secure_filename

import pdfplumber
import string
from nltk.tokenize import RegexpTokenizer
from gensim import corpora
from gensim.models import LsiModel
from gensim import similarities

from gensim.models.ldamodel import LdaModel
import pyLDAvis.gensim_models


data_collection = []
for i in range(len(os.listdir("static\\literature"))):
    with open(f"text\\document{i}.txt","r",encoding="utf-8") as f: 
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
model = LsiModel(corpus, id2word=dictionary, num_topics=10)


app = Flask(__name__,static_folder=os.path.abspath("static/"))


@app.route("/")
def handle_index():
    if "message" in request.args:
        vec_lsi=model[dictionary.doc2bow(process(request.args["message"]))]
        index = similarities.MatrixSimilarity(model[corpus])
        sims = index[vec_lsi]
        sims = sorted(enumerate(sims), key=lambda item: -item[1])
        return send_from_directory("static\\literature", f"document{sims[0][0]}.pdf")
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