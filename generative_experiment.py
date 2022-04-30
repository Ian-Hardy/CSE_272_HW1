import sys
import lucene
import math

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
#tf-idf
from org.apache.lucene.search.similarities import ClassicSimilarity
from org.apache.pylucene.search.similarities import PythonClassicSimilarity
#boolean
from org.apache.lucene.search.similarities import BooleanSimilarity


# tf
class TFSimilarity(PythonClassicSimilarity):
    def __init__(self):
        super().__init__()

    def idf(self, docFreq, numDocs):
        return 1.0

# relevance feedback
# https://stackoverflow.com/questions/15708439/implement-feedback-in-lucene
def addDoc(w, title, isbn):
    doc = Document()
    doc.add(TextField("title", title, Field.Store.YES))
    doc.add(StringField("isbn", isbn, Field.Store.YES))
    w.addDocument(doc)

if __name__ == "__main__":
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
    file2 = open('queries_extended.txt', 'r')
    Lines = file2.readlines()
    i_found = False
    t_found = False
    i_val = None
    t_val = None
    strings = []
    queries = {}
    for i, line in enumerate(Lines):
        if line.startswith('ID: '):
            i_val = line.split('ID: ')[1].strip()
            i_found = True
            queries[i_val] = []
            line_count = 0
            continue
        if i_found:
            if line_count >= 5:
                continue
            line_count += 1
            queries[i_val].append(line)
    
    for qid in queries.keys():
        q_docs = {}
        doc_counts = {}
        for text in queries[qid]:
            text = text.replace('(', ' ')
            text = text.replace(')', ' ')
            text = text.replace('[', ' ')
            text = text.replace(']', ' ')
            text = text.replace('/', ' ')
            text = text.replace('"', ' ')
            text = text.replace('AND', ' ')
            text = text.replace('-', ' ')
            text = text.replace('*', ' ')
            
            try:
                q = QueryParser("title", analyzer).parse(text)
            except:
                continue
            hitsPerPage = 50
            reader = DirectoryReader.open(index)
            searcher = IndexSearcher(reader)
            searcher.setSimilarity(sim)
            docs = searcher.search(q, hitsPerPage)
            hits = docs.scoreDocs
            
            for j in range(len(hits)):
                docId = hits[j].doc
                score = hits[j].score
                d = searcher.doc(docId)
                if d.get("isbn") not in q_docs: 
                    q_docs[d.get("isbn")] = score
                    doc_counts[d.get("isbn")] = 1
                else:
                    q_docs[d.get("isbn")] += score
                    doc_counts[d.get("isbn")] += 1
            reader.close()

        for key in q_docs.keys():
            q_docs[key] = q_docs[key]/doc_counts[key]
        
        sorted_docs = {k: v for k, v in sorted(q_docs.items(), key=lambda item: item[1], reverse=True)}
        top_docs = list(sorted_docs.keys())[:50]
        # QueryID Q0 DocID Rank Score RunID
        for j in range(len(top_docs)):
                string = ''
                string += '{} Q0 '.format(qid)
                string += '{} '.format(top_docs[j])
                string += '{} '.format(j+1)
                string += '{:.6f} '.format(sorted_docs[top_docs[j]])
                string += '{}'.format('generative')
                strings.append(string)
    print(strings)
    f = open("generative_run.txt", "w")
    for i in range(len(strings)):
        if i<len(strings)-1:
            f.write(strings[i]+'\n')
        else:
            f.write(strings[i])