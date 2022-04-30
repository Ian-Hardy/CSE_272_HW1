
# indexer.py
import sys
import lucene

import org.apache.lucene.analysis.standard.StandardAnalyzer
import org.apache.lucene.document.Document
import org.apache.lucene.document.Field
import org.apache.lucene.document.StringField
import org.apache.lucene.document.TextField
import org.apache.lucene.index.DirectoryReader
import org.apache.lucene.index.IndexReader
import org.apache.lucene.index.IndexWriter
import org.apache.lucene.index.IndexWriterConfig
import org.apache.lucene.queryparser.classic.ParseException
import org.apache.lucene.queryparser.classic.QueryParser
import org.apache.lucene.search.IndexSearcher
import org.apache.lucene.search.Query
import org.apache.lucene.search.ScoreDoc
import org.apache.lucene.search.TopDocs
import org.apache.lucene.store.Directory
import org.apache.lucene.store.ByteBuffersDirectory

def addDoc(w, title, isbn):
    doc = Document()
    doc.add(new TextField("title", title, Field.Store.YES))
    doc.add(new StringField("isbn", isbn, Field.Store.YES))
    w.addDocument(doc)

if __name__ == "__main__":
    lucene.initVM()

    # 0. Specify the analyzer for tokenizing text.
    #The same analyzer should be used for indexing and searching
    analyzer = StandardAnalyzer()

    # 1. create the index
    index = ByteBuffersDirectory()

    config = IndexWriterConfig(analyzer)

    w = new IndexWriter(index, config)
    addDoc(w, "Lucene in Action", "193398817")
    addDoc(w, "Lucene for Dummies", "55320055Z")
    addDoc(w, "Managing Gigabytes", "55063554A")
    addDoc(w, "The Art of Computer Science", "9900333X")
    w.close()

    # 2. query
    querystr = "lucene"

    # // the "title" arg specifies the default field to use
    # // when no field is explicitly specified in the query.
    q = QueryParser("title", analyzer).parse(querystr)

    # // 3. search
    hitsPerPage = 10
    reader = DirectoryReader.open(index)
    searcher = new IndexSearcher(reader)
    docs = searcher.search(q, hitsPerPage)
    hits = docs.scoreDocs

    # // 4. display results
    print("Found " + len(hits) + " hits.");
    for i in range(len(hits)):
        docId = hits[i].doc
        Document d = searcher.doc(docId)
        print((i + 1) + ". " + d.get("isbn") + "\t" + d.get("title"))
    }

    # // reader can only be closed when there
    # // is no need to access the documents any more.
    reader.close()