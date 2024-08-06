import re

from spacy.language import Language
from spacy.tokens import Doc, Token
import re
from spacy.language import Language
from spacy.tokens import Doc

# Define a custom lemmatization function
@Language.component(name="_lemmatizer")
def custom_lemmatizer_function(doc):
    for token in doc:
        if token.norm_ == "data":
            token.lemma_ = "data"
    # Add more custom rules for other words if needed
    return doc


@Language.component('_paragrapher')
def assign_paragraph_spans(doc: Doc):
    spans = []
    start = 0
    for token in doc:
        if token.text.count("\n") > 1 and token.is_sent_end:
            spans.append(doc[start:token.i-1])
            start = token.i+1
    doc.spans['paragraphs'] = spans 
    return doc

@Language.component('_sentencizer')   
def sentencize(doc):
    if not Token.has_extension('sent_start'):
        Token.set_extension("sent_start", default=None)  
    spans = []
    #TODO: Handle Edge Cases regarding "et al.," and multiple et als in a sentence
    expression = r'([A-Z][^.!?]*[.!?])(?![A-Z][a-z]\.)(?!\w\.\w.)'

    # Use the regex pattern to split the document text into sentences
    for finding in re.finditer(expression, doc.text):
        start, end = finding.span()
        sentence_span = doc.char_span(start, end)

        # Identify potential sentence boundaries
        if sentence_span is not None:
            first, last = (sentence_span[0].i, sentence_span[-1].i+1)


            sentence = doc[first:last]

            # Base case: No NOUN or VERB in sentence
            has_noun = False
            has_verb = False

            # Check within the sentence bondaries at least a noun AND a verb occur.
            for token in sentence:
                if token.pos_ == 'NOUN':
                    has_noun = True
                elif token.pos_ in 'VERB':
                    has_verb = True

            # If both a noun and a verb are present, add the sentence to the list of spans and set is_sent_start-value for each token.
            if has_noun and has_verb:
                spans.append(doc[first:last])
                # Set sent_start as custom attribute for each token due to conflicts with the default sent_start attribute.
                
                sentence_span[0]._.sent_start = True
                for token in sentence_span[1:-1]:
                    token._.sent_start = False
    
    doc.spans['sentences'] = spans
    return doc


