import pickle
import spacy
import re
from config import config

nlp = spacy.load(config['preprocessing']['TOKENIZER'])

class Sentence:
    '''
    A class to represent a sentence. Sentences have multiple attributes. 
    The attributes are derived from the text of the sentence.

    Attributes
    ----------
    text : str
        The text of the sentence.
    tokens : list
        A list of tuples. Each tuple contains a token and its part of speech.
    inventory : dict
        A dictionary of the tokens and their counts.
    is_valid : bool
        A boolean indicating whether the sentence is valid. A sentence is valid, 
        if it contains at least one noun and one verb, and does not contain a citation.
    '''

    def __init__(self, sentence):
        self.text = sentence
        self.tokens = self.tokenize()
        self.inventory = self.inventize()
        self.is_valid = self.check_validity()


    def tokenize(self):
        return [(word.text, word.pos_) for word in nlp(self.text)]
    
    def inventize(self):
        inventory = {}
        for _, value in self.tokens:
            inventory[value] = inventory.get(value, 0) + 1
        return inventory
    
    def check_validity(self):
        word_types = self.inventory.keys()
        
        if 'NOUN' in word_types \
            and 'VERB' or 'AUX' in word_types \
            and not re.match(r'\(cid:\d{1,4}\)', self.text):
            #and not re.match(r'\(cid:\d{1,4}\)', self.text): \ #adidtional exclusions may be added later on here.
            return True
        else:
            return False
    
    def summarize(self, show_token_details=False):
        print(f'The sentence is:\n{self.text}')
        print(f'The inventory holds:\n{self.inventory}')
        if show_token_details:
            print(f'The token details are:\n{self.tokens}')
    
    def get_details(self):
        # return self.text, self.tokens, self.inventory, self.is_valid 
        # as a dictionary for the sentence.        
        result = {'text': self.text,
                'tokens': self.tokens,
                'inventory': self.inventory,
                'is_valid': self.is_valid
                }
        return result