import psycopg2
import json
import os
from dotenv import load_dotenv
import pandas as pd


load_dotenv()
port = os.getenv("DB_PORT")
user = os.getenv("DB_USER")
host = os.getenv("DB_HOST")
password = os.getenv("DB_PASSWORD")
dbname = os.getenv("DB_DBNAME")


create_table_statement = """
    drop table if exists knowledge;
    create table knowledge (
        id SERIAL PRIMARY KEY,
        quote TEXT NOT NULL,
        author VARCHAR(255) NOT NULL,
        year CHAR(4) NOT NULL
);
"""

create_accuracy_table = """
    DROP TABLE IF EXISTS accuracy;
    CREATE TABLE accuracy(
        id SERIAL PRIMARY KEY,
        MRR float,
        Hit_Rate float
);
"""     

create_ground_truth_table = """
    DROP TABLE IF EXISTS ground_truth;
    CREATE TABLE ground_truth(
        id SERIAL PRIMARY KEY,
        question TEXT NOT NULL,
        quote_id INTEGER
);
"""     


def setup_all_db():
    conn = psycopg2.connect(host=host, port=port, user=user, password=password)
    conn.autocommit = True
    cursor = conn.cursor()
 
    cursor.execute("""
        DROP DATABASE IF EXISTS knowledge_db;
    """)

    cursor.execute("""
        CREATE DATABASE knowledge_db;
    """)

    cursor.close()
    conn.commit()
    conn.close()

    conn = psycopg2.connect(host=host, dbname=dbname, port=port, user=user, password=password)
    cursor = conn.cursor()

    cursor.execute(create_table_statement)
    cursor.execute(create_accuracy_table)
    cursor.execute(create_ground_truth_table)

    cursor.close()
    conn.commit()
    conn.close()


def update_knowledge_table(path):
    conn = psycopg2.connect(host=host, dbname=dbname, port=port, user=user, password=password)

    with conn.cursor() as cursor:
        insert_query = """
            INSERT INTO knowledge (quote, author, year) 
            VALUES (%s, %s, %s)
        """
        
        with open(path, 'r', encoding='utf-8') as file:
            data = json.load(file)

        for entry in data:
            quote = entry['quote']
            author = entry['author']
            year = entry['year']

            cursor.execute(insert_query, (quote, author, year))

        conn.commit()

    conn.close()


def update_ground_truth_table(path):
    conn = psycopg2.connect(host=host, dbname=dbname, port=port, user=user, password=password)

    with conn.cursor() as cursor:
        insert_query = """
            INSERT INTO ground_truth
                (question, quote_id) 
            VALUES 
                (%s, %s)
        """
        
        data = pd.read_csv(path)
        for index, question in zip(data["quote_id"], data["question"]):
            cursor.execute(insert_query, (question, index))

        conn.commit()

    conn.close()


def update_accuracy_table(accuracy_data):
    accuracies = ["MRR", "Hit_Rate"]
    
    query_data = []
    for accuracy in accuracies:
        query_data.append(accuracy_data[accuracy])

    conn = psycopg2.connect(host=host, dbname=dbname, port=port, user=user, password=password)

    with conn.cursor() as cursor:
        insert_query = """
            INSERT INTO accuracy (MRR, Hit_Rate)
            VALUES (%s, %s)
        """

        cursor.execute(insert_query, query_data)

        conn.commit()

    conn.close()


def read_knowledge_table():
    conn = psycopg2.connect(host=host, dbname=dbname, port=port, user=user, password=password)

    with conn.cursor() as cursor:
        select_query = """
            SELECT * FROM knowledge;
        """
    
        cursor.execute(select_query)
        data = cursor.fetchall()

    conn.close()

    quotes = []
    for id, quote, author, year in data:
        quotes.append(
            {
                "id": id,
                "quote": quote,
                "author": author,
                "year": year
            }
        )

    return quotes


def read_ground_truth_table():
    conn = psycopg2.connect(host=host, dbname=dbname, port=port, user=user, password=password)

    with conn.cursor() as cursor:
        select_query = """
            SELECT * FROM ground_truth;
        """
    
        cursor.execute(select_query)
        data = cursor.fetchall()

    conn.close()

    test_quotes = {}
    for id, question, quote_id in data:
        test_quotes[question] = test_quotes.get(question, []) + [quote_id]

    return test_quotes
