import re
from Sentence import Sentence

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
    fields : list  
        A list of the fields of the document. This can be considered as meta-data.
    file : str 
        The file path of the document.
    is_valid : bool
        A boolean indicating whether the document is a valid pdf. 
        A document is valid if it is a pdf and if it contains text.
    raw_text : str
        The raw text of the document. This is only available if the document is a pdf.
    raw_sentences : list
        A list of the sentences of the document. This is only available if the document is a pdf.
    text : list
        A list of the sentences of the document. This is only available if the document is a pdf.

    '''

    def __init__(self, entry, split_text, store_sentences, base_path='/Users/paul/Zotero/storage/'):
        self.base_path = base_path
        self.entry = entry
        self.title = self.entry.fields['title']
        self.fields = self.entry.fields.keys()
        self.sentences = []
        self.is_valid = False             #set is_valid to False by default. This will be set to True if the document is a pdf and if it contains text.
        
        # retrieve file name from entry key 'file'.
        if 'file' in self.fields:
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
        
        if self.is_valid \
            and self.raw_text is not None \
            and self.raw_text != '' \
            and split_text:                             #check if text is not empty and clean_text is set to true. Clean text is set to False by default.
                self.raw_sentences = self.split_text_into_sentences()
                if store_sentences:
                    self.sentences = self.store_sentences()



    def split_text_into_sentences(self):
        
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

        return cleaned_sentences

    def store_sentences(self):
        # filter out invalid sentences and return rejoined text.
        sentences = []
        for sentence in self.raw_sentences:
            sentence = Sentence(sentence)
            if sentence.is_valid:
                sentences.append(sentence)
        
        return sentences


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
    


