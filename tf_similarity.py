import sys
import lucene
import math
import time

from org.apache.lucene.analysis.standard import StandardAnalyzer
from org.apache.lucene.document import Document
from org.apache.lucene.document import Field
from org.apache.lucene.document import StringField
from org.apache.lucene.document import TextField
from org.apache.lucene.index import DirectoryReader
from org.apache.lucene.index import IndexReader
from org.apache.lucene.index import IndexWriter
from org.apache.lucene.index import IndexWriterConfig
from org.apache.lucene.queryparser.classic import ParseException
from org.apache.lucene.queryparser.classic import QueryParser
from org.apache.lucene.search import IndexSearcher
from org.apache.lucene.search import Query
from org.apache.lucene.search import ScoreDoc
from org.apache.lucene.search import TopDocs
from org.apache.lucene.store import Directory
from org.apache.lucene.store import ByteBuffersDirectory
from org.apache.lucene.search.similarities import Similarity
from org.apache.lucene.analysis.en import EnglishAnalyzer
from org.apache.pylucene.search.similarities import PythonClassicSimilarity

class TFSimilarity(PythonClassicSimilarity):
    def __init__(self):
        super().__init__()

    def idf(self, docFreq, numDocs):
        return 1.0

def addDoc(w, title, isbn):
    doc = Document()
    doc.add(TextField("title", title, Field.Store.YES))
    doc.add(StringField("isbn", isbn, Field.Store.YES))
    w.addDocument(doc)

if __name__ == "__main__":
    start = time.time()
    lucene.initVM()

    # 0. Specify the analyzer for tokenizing text.
    #The same analyzer should be used for indexing and searching
    stopWords = EnglishAnalyzer.getDefaultStopSet()
    analyzer = StandardAnalyzer(stopWords)

    # 1. create the index
    index = ByteBuffersDirectory()
    sim = TFSimilarity()
    config = IndexWriterConfig(analyzer)
    config.setSimilarity(sim)

    w = IndexWriter(index, config)

    # Retrieve documents
    file1 = open('ohsumed.88-91', 'r')
    Lines = file1.readlines()
    i_found = False
    t_found = False
    i_val = None
    t_val = None
    for i, line in enumerate(Lines):
        if line[:2] == '.U':
            i_val = Lines[i+1].strip('\n')
            i_found = True
        if line.strip() == '.W':
            t_val = Lines[i+1]
            t_found = True
        if i_found and t_found:
            i_found = False
            t_found = False
            addDoc(w, t_val, i_val)
    w.close()

    # 2. query
    file2 = open('query.ohsu.1-63', 'r')
    Lines = file2.readlines()
    i_found = False
    t_found = False
    i_val = None
    t_val = None
    strings = []
    for i, line in enumerate(Lines):
        if line[:5] == '<num>':
            i_val = line.split(' ')[2].strip()
            i_found = True
        if line[:6] == '<desc>':
            t_val = Lines[i+1].replace('/', ' ')
            t_found = True
        
        if i_found and t_found:
            i_found = False
            t_found = False

            # place query in parser
            q = QueryParser("title", analyzer).parse(t_val)

            # // 3. search
            hitsPerPage = 50
            reader = DirectoryReader.open(index)
            searcher = IndexSearcher(reader)
            searcher.setSimilarity(sim)
            docs = searcher.search(q, hitsPerPage)
            hits = docs.scoreDocs
            # QueryID Q0 DocID Rank Score RunID
            for j in range(len(hits)):
                string = ''
                string += '{} Q0 '.format(i_val)
                docId = hits[j].doc
                score = hits[j].score
                d = searcher.doc(docId)
                string += '{} '.format(d.get("isbn"))
                string += '{} '.format(j+1)
                string += '{:.6f} '.format(score)
                string += '{}'.format('tf')
                strings.append(string)
            reader.close()
    
    f = open("tf_run.txt", "w")
    for i in range(len(strings)):
        if i<len(strings)-1:
            f.write(strings[i]+'\n')
        else:
            f.write(strings[i])
    end = time.time()
    print(end-start)