from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
from pypdf import PdfReader
from groq import Groq
import psycopg2
from psycopg2.extras import execute_values
import os


client =  Groq(
    api_key=os.environ.get("GROK_KEY")
)

model=SentenceTransformer("all-MiniLM-L6-v2")  

splitter = RecursiveCharacterTextSplitter(
    chunk_size=100, 
    chunk_overlap=20
)
CONNECTION_STRING = os.getenv("CONNECTION_STRING")

conn = psycopg2.connect(CONNECTION_STRING)

with open("prompt.txt", "r") as file:
    base_prompt = file.read()


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
                chunk TEXT NOT NULL,
                page_number INT NOT NULL,
                embedding vector(384) NOT NULL
                );
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
        context = ""                       
        
        cur.execute(
            """
            SELECT chunk FROM vectors 
            WHERE embedding <=> %s:: vector < 0.5
            LIMIT 5;
            """,
            (embedded_question,)
        )
        
        for chunk in cur.fetchall():
            context += "\n" + chunk[0]
    
    prompt = base_prompt.format(
        context = context,
        question = question
    )
    
    response = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content":prompt,
            }
        ],
        model="openai/gpt-oss-120b",

    )
    return response.choices[0].message.content


def process_file(path: str)->None:

    reader = PdfReader(path)
    pages = []
    list_of_chunks = []
    for page in reader.pages:
        text = page.extract_text(
                        extraction_mode="layout",
           layout_mode_space_vertically=False,
        ).replace("\0","") #removing possible null terminators/SQL won't accept them
        
        chunks = splitter.split_text(text)
        list_of_chunks.extend(chunks)

        for c in chunks:
            pages.append(page.page_number)
    
    embeddings = vector_text(list_of_chunks)
    sequences = (list(zip(embeddings,list_of_chunks, pages)))
        
    stmnt = "INSERT INTO vectors (embedding, chunk, page_number) VALUES %s"
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

           






    











