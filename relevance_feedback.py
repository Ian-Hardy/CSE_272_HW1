# indexer.py
import sys
import lucene
import math
import time

from org.apache.lucene.analysis.standard import StandardAnalyzer
from org.apache.lucene.analysis import TokenStream
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
from org.apache.lucene.analysis.tokenattributes import CharTermAttribute
from org.apache.lucene.analysis.en import EnglishAnalyzer
from org.apache.lucene.search.similarities import ClassicSimilarity

# relevance feedback
# https://stackoverflow.com/questions/15708439/implement-feedback-in-lucene
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

    # to be used for getting terms from docs later
    def analyze(text, analyzer):
        #print(text)
        result = []
        ts = analyzer.tokenStream(None, text)
        ts.reset()
        while (ts.incrementToken()):
            ts_text = ts.reflectAsString(True)
            term = ts_text.split('=')[1].split(',')[0]
            #print(term)
            result.append(term)
        ts.end()
        ts.close()
        return result

    # 1. create the index
    index = ByteBuffersDirectory()
    sim = ClassicSimilarity()
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
            hitsPerPage = 20
            reader = DirectoryReader.open(index)
            searcher = IndexSearcher(reader)
            searcher.setSimilarity(sim)
            docs = searcher.search(q, hitsPerPage)
            hits = docs.scoreDocs

            # Get terms from top 20 results
            # Rank top terms
            terms = {}
            for j in range(len(hits)):
                docId = hits[j].doc
                d = searcher.doc(docId)
                text = d.get("title")
                terms_ = analyze(text, analyzer)
                for term in terms_:
                    if term not in terms.keys():
                        terms[term] = 1
                    else:
                        terms[term] += 1
            sorted_terms = {k: v for k, v in sorted(terms.items(), key=lambda item: item[1], reverse=True)}
            top_terms = list(sorted_terms.keys())[:15]
            
            new_query = t_val
            for term in top_terms:
                new_query += ' '+term

             # place query in parser
            q = QueryParser("title", analyzer).parse(new_query)

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
                string += '{}'.format('Relevance')
                strings.append(string)
            reader.close()
    
    f = open("relevance_run.txt", "w")
    for i in range(len(strings)):
        if i<len(strings)-1:
            f.write(strings[i]+'\n')
        else:
            f.write(strings[i])
    end = time.time()
    print(end-start)