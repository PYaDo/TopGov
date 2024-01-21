import re
import spacy
from pybtex import database
from pdfminer.high_level import extract_text

nlp = spacy.load("en_core_web_trf")

class Library:

    def __init__(self, path, format='bibtex'):
        self.path = path
        self.library = database.parse_file(path, bib_format=format)
        self.entries = []
        for entry in self.library.entries:
            self.entries.append(self.library.entries[entry])


class Document():

    def __init__(self, entry):
        base_path = '/Users/paul/Zotero/storage/' 
        self.entry = entry
        self.title = self.entry.fields['title']
        self.fields = self.entry.fields.keys()
        if 'file' in self.fields:
           self.file = self.entry.fields['file'].split(base_path)[1].split(':')[0]
        else:
            self.file = ''
        self.is_pdf = bool(re.search('.pdf', self.file))
        if self.is_pdf:
            self.raw_text = extract_text(base_path + self.file)
            self.sentences = self.get_sentences()
            self.text = self.get_text()
            self.is_valid = True
        else:
            self.is_valid = False

    def get_sentences(self):
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
        sentences = cleaned_sentences
        return sentences
        
    def get_text(self):
        text = []
        for sentence in self.sentences:
            sentence = Sentence(sentence)
            if sentence.is_valid:
                text.append(sentence.raw_text)
        return text

class Sentence:
    def __init__(self, sentence):
        self.raw_text = sentence
        self.tokens = self.tokenize()
        self.inventory = self.inventize()
        self.is_valid = self.check_validity()
        


    def tokenize(self):
        return [(word.text, word.pos_) for word in nlp(self.raw_text)]
    
    def inventize(self):
        inventory = {}
        for _, value in self.tokens:
            inventory[value] = inventory.get(value, 0) + 1
        return inventory
    
    def check_validity(self):
        word_types = self.inventory.keys()
        
        if 'NOUN' in word_types \
            and 'VERB' in word_types \
            and not re.match(r'\(cid:\d{1,4}\)', self.raw_text):
            return True
        else:
            return False
    
    def summarize(self, show_token_details=False):
        print(f'The sentence is:\n{self.raw_text}')
        print(f'The inventory holds:\n{self.inventory}')
        if show_token_details:
            print(f'The token details are:\n{self.tokens}')