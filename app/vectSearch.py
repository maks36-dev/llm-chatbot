import os
from dotenv import load_dotenv
from db import read_knowledge_table, read_ground_truth_table, update_accuracy_table
from metrics import *

from elasticsearch import Elasticsearch
from sentence_transformers import SentenceTransformer


load_dotenv()
host = os.getenv("ES_HOST")
port = os.getenv("ES_PORT")

# load the sentence transformer
current_directory = os.getcwd()
model = SentenceTransformer(os.path.join(current_directory, 'saved_models/'))


es_client = Elasticsearch(f'http://{host}:{port}')

index_settings = {
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0
    },
    "mappings": {
        "properties": {
            "id": {"type": "integer"},
            "quote": {"type": "text"},
            "author": {"type": "text"},
            "year": {"type": "text"},
            "data_vector": {"type": "dense_vector", "dims": 768, "index": True, "similarity": "cosine"},
            "quote_vector": {"type": "dense_vector", "dims": 768, "index": True, "similarity": "cosine"},
            "author_vector": {"type": "dense_vector", "dims": 768, "index": True, "similarity": "cosine"}
        }
    }
}
index_name = "quote-questions"

# create elastic search db and index
def create_elastic_db():
    global index_settings, index_name

    es_client.indices.delete(index=index_name, ignore_unavailable=True)
    es_client.indices.create(index=index_name, body=index_settings)


def convert_to_index():
    data = read_knowledge_table()

    for doc in data:
        doc["data_vector"] = model.encode(doc["quote"] + doc["author"] + str(doc["year"]))
        doc["quote_vector"] = model.encode(doc["quote"])
        doc["author_vector"] = model.encode(doc["author"])
        try:
            es_client.index(index=index_name, document=doc)
        except Exception as e:
            ...


def init_es():
    create_elastic_db()
    convert_to_index()


# elastic vector search function
def elastic_search_vector(query: str, k: int=2, field="data_vector"):
    vector_search_query = model.encode(query)

    query = {
        "field": field,
        "query_vector": vector_search_query,
        "k": k,
        "num_candidates": 10000, 
    }

    response = es_client.search(index=index_name, knn=query, source=["quote", "author", "year", "id"])

    quotes = []
    for hit in response['hits']['hits']:
        quote = hit['_source']
        quotes.append({
            "quote": quote["quote"], 
            "author": quote["author"], 
            "year": quote["year"], 
            "id": quote["id"],
            "_score": hit["_score"]
        })

    return quotes


# calculating metrics
def get_quotes_ids(question, k: int=3):
    ids = []

    prediction_quotes = [
        elastic_search_vector(question, k, field="data_vector"),
        elastic_search_vector(question, k, field="quote_vector"),
        elastic_search_vector(question, k, field="author_vector"),
    ]

    for quotes in zip(*prediction_quotes):
        best_quote_id = np.argmax(np.array(list(map(lambda q: q["_score"], quotes)))) # calculating best quote using '_score'
        ids.append(quotes[best_quote_id]["id"])

    return (question, ids)


def calculate_accuracy():
    ground_truth = read_ground_truth_table()

    predictions = {}
    for question in ground_truth.keys():
        question, ids = get_quotes_ids(question)
        predictions[question] = ids

    accuracy = {
        "MRR": mean_reciprocal_rank(ground_truth, predictions),
        "Hit_Rate": hit_rate(ground_truth, predictions)
    }

    update_accuracy_table(accuracy)


# generation of promt
def generate_promt(question, k: int=1):
    prediction_quotes = [
        elastic_search_vector(question, k, field="data_vector"),
        elastic_search_vector(question, k, field="quote_vector"),
        elastic_search_vector(question, k, field="author_vector"),
    ]

    new_promt = f"""
Question or statement: {question}


Choose the quote that best fits the user's question or statement and return in such format: "Quote. Author. Year"

Differents quotes:

"""
    used = set()
    for prediction in prediction_quotes:
        for quote in prediction:
            if quote["id"] not in used:
                new_promt += f"-- Quote: {quote['quote']}\nAuthor: {quote['author']}\nYear: {quote['year']}\n\n"
            used.add(quote["id"])

    return new_promt
