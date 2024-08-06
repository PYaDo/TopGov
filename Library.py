import os
import json
import hashlib
import spacy
import pickle

import spacy_transformers
import CustomComponents

import numpy as np

from spacy.tokens import DocBin, Doc
from tqdm.notebook import tqdm

from transformers import AutoTokenizer
from sentence_transformers import SentenceTransformer
from adapters import AutoAdapterModel

from config import config
from pybtex import database
from pdfminer.high_level import extract_text  # For extracting text from PDF files.


class Library:
    """
    A class to represent a library of documents.
    """

    # Add custom attributes to the Doc object.
    if not Doc.has_extension("year"):
        Doc.set_extension("year", default=None)

    source_path = config["serialization"]["folder_path"]
    library_folder_path = config["library"]["folder_path"]

    nlp = spacy.load(config["tokenizer"]["model"])

    # Add the custom lemmatizer to the pipeline
    nlp.add_pipe("_lemmatizer", name="_lemmatizer", after="lemmatizer")

    # Deprecated: Add custom components to the pipeline.
    # for component in config['pipeline']['custom_components'].split(', '):
    #     nlp.add_pipe(component, last=True)
    # print('Active pipline components:', nlp.pipe_names)

    nlp.config.to_disk(
        "pipeline/config.cfg"
    )  # Save the pipeline configuration to repo directory.

    def __init__(
        self,
        lib_path: str,
        format: str = "bibtex",
        source: str = "abstract",  # Choose between 'abstract' or 'paper' document source.
        granularity: str = "sentence",  # Choose between 'fulltext' or 'abstract' document source.
        sample_size=None,
        is_test=False,
    ):

        self.granularity = granularity
        self.source = source
        self.sample_size = sample_size
        self.is_test = is_test
        self.format = format

        if is_test:
            test = "test"
        else:
            test = ""

        self.serialized_entries_path = os.path.join(
            self.source_path, test, source, granularity
        )
        print(f"Library folder path: {self.serialized_entries_path}")

        # Load the library from the specified path.
        entries = database.parse_file(lib_path, bib_format=format).entries

        # Get the entries from the library.
        entries = [entries[entry] for entry in entries]

        # Get a sample of the entries if specified (aka the "sample_size is not None").
        self.entries = entries[:sample_size] if sample_size is not None else entries

        self.docs = []

    def write_serialized_entry(
        self, entry_title: str, file_name="serialized_entries.json"
    ):
        file_path = os.path.join(self.serialized_entries_path, file_name)

        data = self.read_serialized_entries()

        entry_title_hash = hashlib.sha256(entry_title.encode()).hexdigest()

        data[entry_title_hash] = entry_title

        with open(file_path, "w") as file:
            json.dump(data, file)

        return data

    def read_serialized_entries(self, file_name="serialized_entries.json"):
        file_path = os.path.join(self.serialized_entries_path, file_name)

        if not os.path.exists(file_path):
            os.makedirs(self.serialized_entries_path, exist_ok=True)
            with open(file_path, "w") as file:
                json.dump({}, file)

        file_path = os.path.join(self.serialized_entries_path, file_name)
        with open(file_path, "r") as file:
            data = json.load(file)
        return data

    def paragraphs(self, doc: Doc):
        start = 0
        for token in doc:
            if token.is_space and token.text.count("\n") > 1:
                yield doc[start : token.i]
                start = token.i
        yield doc[start:]

    def serialize(self):

        serialized_entries_keys = self.read_serialized_entries().keys()
        entries = [
            entry
            for entry in self.entries
            if hashlib.sha256(entry.fields["title"].encode()).hexdigest()
            not in serialized_entries_keys
        ]

        for entry in tqdm(entries, desc="Serializing files...", leave=True):

            entry_title_hash = hashlib.sha256(
                entry.fields["title"].encode()
            ).hexdigest()

            if entry_title_hash not in serialized_entries_keys:

                if self.source == "abstract" and "abstract" in entry.fields.keys():
                    text = entry.fields["abstract"]
                elif self.source == "paper" and "file" in entry.fields.keys():
                    file = (
                        entry.fields["file"]
                        .split(self.library_folder_path)[1]
                        .split(":")[0]
                    )
                    text = extract_text(
                        "".join([self.library_folder_path, file])
                    ).strip()
                else:
                    print(f'No text found for entry: {entry.fields["title"]}.')
                    continue

                nlp_doc = self.nlp(text)

                doc_bin = DocBin(store_user_data=False)

                if self.granularity == "sentence":
                    for sent in nlp_doc.sents:
                        doc_bin.add(sent.as_doc())
                elif self.granularity == "paragraph":
                    for par in self.paragraphs(nlp_doc):
                        doc = par.as_doc()
                        doc_bin.add(doc)
                elif self.granularity == "fulltext":
                    doc_bin.add(nlp_doc)

                doc_bin.to_disk(
                    os.path.join(
                        self.serialized_entries_path, f"{entry_title_hash}.spacy"
                    )
                )
                self.write_serialized_entry(entry.fields["title"])

        self.nlp.vocab.to_disk("vocab")

        self.deserialize()

    def deserialize(self):

        self.docs = []

        nlp_vocab = spacy.vocab.Vocab().from_disk("vocab")
        serialized_entries = self.read_serialized_entries().keys()

        counter = 0
        for entry in tqdm(self.entries, desc="Deserializing files...", leave=True):
            entry_title_hash = hashlib.sha256(
                entry.fields["title"].encode()
            ).hexdigest()
            if entry_title_hash in serialized_entries:
                doc_bin = DocBin().from_disk(
                    os.path.join(
                        self.serialized_entries_path, f"{entry_title_hash}.spacy"
                    )
                )

                docs = list(doc_bin.get_docs(nlp_vocab))
                for doc in docs:
                    missing_year = False
                    try:
                        doc._.year = entry.fields["year"]
                    except KeyError:
                        missing_year = True

                        doc._.year = "0000"
                    self.docs.append(doc)
                if missing_year:
                    print(f'No year found for entry: {entry.fields["title"]}.')
                counter += 1
            else:
                continue

        print(f"Successfully deserialized {counter} entries.")

    def delete_serialized_entries(self):

        confirmation = input(
            f"Are you sure you want to delete all serialized files in {self.serialized_entries_path}? (Y/n): "
        ).strip()
        if confirmation == "Y":
            try:
                files = os.listdir(self.serialized_entries_path)
                for file in files:
                    file_path = os.path.join(self.serialized_entries_path, file)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                print("All serialized files deleted successfully.")
            except OSError:
                print("Error occurred while deleting files.")
        elif confirmation == "n":
            print("Deletion canceled.")
        else:
            print("Invalid input. Please try again.")

    def set_stopwords(self, stopwords: list):
        self.stopwords = stopwords

    def get_valid_docs(self, docs):
        valid_docs = []
        for doc in docs:
            has_noun = False
            has_verb = False

            for token in doc:
                if token.pos_ == "NOUN":
                    has_noun = True
                elif token.pos_ == "VERB":
                    has_verb = True
                else:
                    continue

            if has_noun and has_verb:
                valid_docs.append(doc)
            else:
                continue
        return valid_docs

    def get_corpus(self, docs):

        corpus = []
        for doc in docs:
            lemmas = " ".join(
                [
                    token.lemma_
                    for token in doc
                    if token.pos_ in ["NOUN", "VERB", "ADJ", "ADV"]
                    and token.lemma_ not in self.stopwords
                ]
            )
            corpus.append(lemmas)

        return corpus

    def precompute_embeddings(
        self, corpus, model_name=config["embedding"]["model_name"]
    ):
        if model_name.split("/")[0] == "sentence-transformers":
            model = SentenceTransformer(model_name)
            embeddings = model.encode(corpus, show_progress_bar=True)
        elif model_name == "allenai/specter2":
            model = AutoAdapterModel.from_pretrained("allenai/specter2")
            # adapter_name = model.load_adapter(model_name, source="hf", set_active=True)

            # preprocess the input
            tokenizer = AutoTokenizer.from_pretrained("allenai/specter2")
            inputs = tokenizer(
                corpus,
                padding=True,
                truncation=True,
                return_tensors="pt",
                return_token_type_ids=False,
                max_length=512,
            )
            output = model(**inputs)
            # take the first token in the batch as the embedding
            embeddings = output.last_hidden_state[:, 0, :]
        else:
            print(
                "Invalid model name. Please provide a valid model name via config.cfg."
            )

        return embeddings

    def save_embeddings(self, validate_docs: bool = True, overwrite=False) -> None:
        # https://www.sbert.net/examples/applications/computing-embeddings/README.html#storing-loading-embeddings
        # Store sentences & embeddings on disc
        if not overwrite:
            print(
                "Overwrite is set to False. Set overwrite to True to overwrite existing embeddings."
            )
            return None

        if validate_docs:
            docs = self.get_valid_docs(self.docs)
        else:
            docs = self.docs

        corpus = self.get_corpus(docs)
        embeddings = self.precompute_embeddings(corpus)

        years = [doc._.year for doc in docs]

        if (
            corpus is not None
            and embeddings is not None
            and len(corpus) == len(embeddings)
        ):
            with open(
                os.path.join(self.serialized_entries_path, "embeddings.pkl"), "wb"
            ) as fOut:
                pickle.dump(
                    {"text": corpus, "year": years, "embeddings": embeddings},
                    fOut,
                    protocol=pickle.HIGHEST_PROTOCOL,
                )
        return None

    def load_embeddings(self) -> tuple:
        # https://www.sbert.net/examples/applications/computing-embeddings/README.html#storing-loading-embeddings
        # Load sentences & embeddings from disc
        if os.path.exists(os.path.join(self.serialized_entries_path, "embeddings.pkl")):
            with open(
                os.path.join(self.serialized_entries_path, "embeddings.pkl"), "rb"
            ) as fIn:
                stored_data = pickle.load(fIn)
                stored_corpus = stored_data["text"]
                stored_years = stored_data["year"]
                stored_embeddings = stored_data["embeddings"]
        else:
            print("No stored embeddings found.")
        return stored_corpus, stored_years, stored_embeddings


def main():
    library = Library(
        config["bibliography"]["test_file_path"],
        sample_size=2,
        source="abstract",
        granularity="paragraph",
    )
    # #library.delete_serialized_entries()
    library.serialize()
    # corpus = library.get_corpus()
    # library.precompute_embeddings(corpus, model_name='sentence-transformers/allenai-specter')
    print(library.entries[0])


if __name__ == "__main__":
    main()
