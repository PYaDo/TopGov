
import os
import json
import hashlib

from config import config
from Document import Document
from pybtex import database


class Library:

    """
    A class to represent a library of documents.

    Attributes
    ----------
    path : str
        The path to the library file.
    format : str
        The format of the library file. Default is 'bibtex'.
    library : pybtex.database.BibliographyData
        The library as a pybtex database.
    entries : list
        A list of the entries in the library.
    """

    docs = []
    entries = []

    def __init__(self, 
                 path, 
                 format='bibtex', 
                 serialize=False):
        
        self.no_entries = len(self.entries) == 0        
        if self.no_entries:
            self.library = database.parse_file(path, bib_format=format)
            for entry in self.library.entries:
                self.entries.append(self.library.entries[entry])

        if serialize:
            self.serialize(retrieve_docs)
    
    def serialize(self, retrieve_docs=True):
        
        self.no_docs = len(self.docs) == 0
        if self.no_docs:
            self.docs = [Document(entry) for entry in self.entries]

        for doc in self.docs:
            print('Processing document: ' + doc.title)
            print('Splitting text into sentences.')
            doc.split_text_into_sentences()
            print('Analyzing sentences.')
            doc.store_sentences()
            print('Serializing document.')
            doc.to_json()

    def deserialize(self, path=config['data']['PATH']):
        for filename in os.listdir(path):
            if filename.endswith('.json'):
                doc = Document()
                doc.from_json(filename)
                print('Successfully deserialized ' + doc.title)
                self.docs.append(doc)
        return

    