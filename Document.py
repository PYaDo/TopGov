import os
import re
import json
import hashlib

from Sentence import Sentence
from config import config
from pathlib import Path
from pdfminer.high_level import extract_text

class Document():
    '''
    A document class. Documents have multiple attributes.
    Documents are based of the pybtex database entry class. 
    They take the entry as an argument and derive the file path for further processing.
    The Document class also sotres the fields of the entry as an attribute-list. 
    Those attributescan be considered as meta-data of the document.

    Attributes
    ----------
    entry : pybtex.database.Entry
        The entry of the document.
    title : str
        The title of the document.
    file : str
        The file name of the document.
    is_valid : bool
        A boolean indicating whether the document is valid. A document is valid,
        if it is a pdf and if it contains text.
    raw_text : str
        The raw text of the document.
    raw_sentences : list
        A list of the raw sentences of the document.
    sentences : list
        A list of the sentences of the document.

    '''

    def __init__(self, entry = None):
        # beaviour during serialization if an entry object is passed.
        try:
            self.base_path = config['library']['storage']
            self.is_valid = False                   # set is_valid to False by default. 
                                                    # This will be set to True if the document 
                                                    # is a pdf and if it contains text.
            self.entry = entry
            self.title = self.entry.fields['title']
            self.raw_sentences = None
            self.sentences = None
            
            # retrieve file name from entry key 'file'.
            if 'file' in self.entry.fields.keys():
                self.file = self.entry.fields['file'].split(self.base_path)[1].split(':')[0]
            else:
                self.file = None 
            
            # extract text for existing pdf files.
            if self.file is not None \
                and self.file.endswith('.pdf') \
                and Path(self.base_path + self.file).exists():
                try:
                    self.raw_text = extract_text(self.base_path + self.file)
                    self.is_valid = True
                except Exception:
                    self.is_valid = False
                    print(f'Could not extract text from {self.base_path + self.file}.')
        except AttributeError as e:
            if entry is None:
                print('No entry object passed on creation of document. Creating empty document. Attributes may be set by deserialization afterwards.')

    def split_text_into_sentences(self):

        if self.is_valid \
            and self.raw_text is not None \
            and self.raw_text != '':
        
            # extract sentences from raw text and split into raw sentences.
            cleaned_sentences = []
            sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s|(\n){2,}', self.raw_text)
            sentences = [sentence.replace('\n',' ') for sentence in sentences if sentence not in [None,'\n','',' ','  ']]
            sentences = [sentence for sentence in sentences if not re.match(r'^[^a-zA-Z]*$', sentence)]
        
            #replace tailing digits on words. those digits are usually footnotes
            sentences = [re.sub(r'[A-Za-z]\d+\b', '', sentence) for sentence in sentences]

            #corp sentence to beginning based on first alphabtic character
            for sentence in sentences:
                for i, char in enumerate(sentence):
                    if char.isalpha() and re.match(r'[A-Z]',char):
                        cleaned_sentences.append(sentence[i:])
                        break
            
            self.raw_sentences = cleaned_sentences
            
            return
        
        else:
            print('''Could not split text into sentences. Either the document is not a valid document or the raw text is empty.''')
            return

    def store_sentences(self):
        if self.raw_sentences is not None \
            and self.raw_sentences != []:
                # filter out invalid sentences and return rejoined text.
                self.sentences = []
                for sentence in self.raw_sentences:
                    sen = Sentence(sentence)
                    if sen.is_valid:
                        self.sentences.append(sen)
                return 
        else:
            print(f'''Could not store sentences. "self.raw_sentences" is None or empty.''')
            return


    def get_sentences(self):
        return [sentence.text for sentence in self.sentences]
    
    def get_text(self):
        sentences = [sentence.text for sentence in self.sentences]
        return ' '.join(sentences)
    
    def get_details(self):
        sentence_details = {}
        for i, sentence in enumerate(self.sentences):
            sentence_details[i] = sentence.get_details()

        result = {'base_path': self.base_path,
                  'title': self.title,
                  'file': self.file,
                  'is_valid': self.is_valid,
                  'raw_text': self.raw_text,
                  'raw_sentences': self.raw_sentences,
                  'sentences': sentence_details
            }
        return result    

    def to_json(self, path_to_serialized_data=config['data']['PATH']):
        print(f'Serializing {self.title}...') 
        content = self.get_details()
        filename = hashlib.sha256(self.title.encode()).hexdigest() + '.json'
        with open(f'{path_to_serialized_data}{filename}', 'w') as f:
            json.dump(content, f, indent=4) 
    
    def from_json(self, filename, path=config['data']['PATH']):
         with open(os.path.join(path, filename), 'r') as f:
            content = json.load(f)
            self.__dict__.update(content)
