
import os
import json
import hashlib

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
                 retrieve_docs=False, 
                 split_text=False, 
                 store_sentences=False, 
                 serialize=False, 
                 verbose=False, 
                 path_to_serialized_data='/Users/paul/Documents/FOM/MasterArbeit/Thesis/dev/data/'):
        self.path = path
        self.verbose = verbose
        self.path_to_serialized_data = path_to_serialized_data
        
        self.no_entries = len(self.entries) == 0        
        if self.no_entries:
            self.library = database.parse_file(path, bib_format=format)
            for entry in self.library.entries:
                self.entries.append(self.library.entries[entry])
        
        self.no_docs = len(self.docs) == 0
        if retrieve_docs and self.no_docs:
            self.docs = [Document(entry, split_text, store_sentences) for entry in self.entries]

        if serialize:
            self.serialize_documents(path_to_serialized_data)

    def serialize_documents(self, path_to_serialized_data):
        for doc in self.docs:
            if self.verbose:
                print(f'Serializing {doc.title}...') 
            content = doc.get_details()
            filename = hashlib.sha256(doc.title.encode()).hexdigest() + '.json'
            with open(f'{path_to_serialized_data}{filename}', 'w') as f:
                json.dump(content, f, indent=4)  
    
    # Deserialize documents
    def deserialize_documents(self, path_to_serialized_data):
        documents = []
        for filename in os.listdir(path_to_serialized_data):
            with open(os.path.join(path_to_serialized_data, filename), 'r') as f:
                content = json.load(f)
                documents.append(content)
    
    