from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
from pypdf import PdfReader
from openai import OpenAI
import psycopg2
from psycopg2.extras import execute_values
import os

client = OpenAI()

splitter = RecursiveCharacterTextSplitter(
    chunk_size=100, 
    chunk_overlap=20
)
CONNECTION_STRING = os.getenv("CONNECTION_STRING")

model = SentenceTransformer('all-MiniLM-L6-v2')

conn = psycopg2.connect(CONNECTION_STRING)

def create_table():
    with conn:
        with conn.cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    with conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS vectors
                (id BIGSERIAL PRIMARY KEY, 
                chunk TEXT, 
                embedding vector(384))
                """
            )
    

def vector_text(chunks):
    embeddings = model.encode(chunks)
    return embeddings.tolist()

def similiar_search(question: str) -> str:
    if not question:
        raise ValueError("No value was entered")

    # embedding question
    embedded_question = vector_text(question)

    with conn.cursor() as cur: 
        result = ""                       
        
        cur.execute(
            """
            SELECT chunk FROM vectors 
            WHERE embedding <=> %s:: vector < 1;
            """,
            (embedded_question,)
        )
        
        for chunk in cur.fetchall():
            result += "\n" + chunk[0]
    
    response = client.responses.create(
            model="gpt-5.4",
            input=f"""
            answer this {question} and only use this {result}
            to formulate an answer.
            """,
    )

    return response.output_text


def load_file(path: str)->None:

    reader = PdfReader(path)
    pages = []
    for page in reader.pages:
        text = page.extract_text(
            extraction_mode="layout",
            layout_mode_space_vertically=False,
        )
        #removing possible null terminators/SQL won't accept them
        cleaned_text = text.replace("\0","")   
        pages.append(cleaned_text)    
    
    chunks = splitter.split_text("\n".join(pages))

    embeddings = vector_text(chunks)

    sequences=list(zip(embeddings, chunks))
    
    stmnt = "INSERT INTO vectors (embedding, chunk) VALUES %s"
    try:
        with conn.cursor() as cur:
            execute_values(cur, stmnt, sequences)
        conn.commit()
        
    except psycopg2.errors.UndefinedTable:
        conn.rollback()
        create_table()
        
        with conn.cursor() as cur:
            execute_values(cur, stmnt, sequences)
        conn.commit()

    return












