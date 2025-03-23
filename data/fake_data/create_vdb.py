import os
import uuid

import qdrant_client
from dotenv import load_dotenv
from langchain.text_splitter import RecursiveCharacterTextSplitter
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct
from sentence_transformers import SentenceTransformer

# Load environment variables from .env file
load_dotenv()

# Initialize Sentence Transformer model for embedding generation
embed_model = SentenceTransformer("BAAI/bge-large-en-v1.5")

# Connect to Qdrant client
client_connection = QdrantClient(url="http://localhost:6333")

# Get embedding dimension (used for setting vector size)
embed_model.get_sentence_embedding_dimension()

# Define vector configuration for Qdrant (cosine similarity)
qdrant_vector_config = qdrant_client.http.models.VectorParams(
    size=1024,  # Dimension of the embedding vector
    distance=qdrant_client.http.models.Distance.COSINE,  # Use cosine distance for similarity
)

# Create Qdrant collection for storing lost package policy data
client_connection.create_collection(
    collection_name="lost_package_policy", vectors_config=qdrant_vector_config
)

# Load content from the lost_package_policy markdown file
with open(
    os.path.join(os.path.dirname(os.getcwd()), "lost_package_policy.md"),
    "r",
    encoding="utf-8",
) as f:
    content = f.read()

# Generate embedding vector for the entire content (optional step, not used in the final upload)
vector = embed_model.encode(content).tolist()

# Split content into smaller chunks (e.g., paragraphs or sections)
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,  # Maximum chunk size in characters
    chunk_overlap=100,  # Overlap between chunks
    separators=["\n\n", "\n", " ", ""],  # Split based on newlines, spaces, etc.
    length_function=len,  # Function to determine length of chunks
)

chunks = text_splitter.split_text(content)

# Embed each chunk and prepare for uploading to Qdrant
points = []
for chunk in chunks:
    # Generate embedding vector for each chunk
    vector = embed_model.encode(chunk).tolist()

    # Generate a unique ID for each chunk (UUID)
    doc_id = str(uuid.uuid4())

    # Create a PointStruct to hold the chunk data and vector
    points.append(PointStruct(id=doc_id, vector=vector, payload={"text": chunk}))

# Upload the chunks to Qdrant collection for lost_package_policy
client_connection.upsert(collection_name="lost_package_policy", points=points)

# Create Qdrant collection for storing shipping information data
client_connection.create_collection(
    collection_name="shipping_information", vectors_config=qdrant_vector_config
)

# Load content from the shipping_information markdown file
with open(
    os.path.join(os.path.dirname(os.getcwd()), "shipping_information.md"),
    "r",
    encoding="utf-8",
) as f:
    content = f.read()

# Generate embedding vector for the entire content (optional step, not used in the final upload)
vector = embed_model.encode(content).tolist()

# Split content into smaller chunks (e.g., paragraphs or sections) for shipping information
chunks = text_splitter.split_text(content)

# Embed each chunk and prepare for uploading to Qdrant
points = []
for chunk in chunks:
    # Generate embedding vector for each chunk
    vector = embed_model.encode(chunk).tolist()

    # Generate a unique ID for each chunk (UUID)
    doc_id = str(uuid.uuid4())

    # Create a PointStruct to hold the chunk data and vector
    points.append(PointStruct(id=doc_id, vector=vector, payload={"text": chunk}))

# Upload the chunks to Qdrant collection for shipping_information
client_connection.upsert(collection_name="shipping_information", points=points)
