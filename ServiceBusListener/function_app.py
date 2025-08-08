import io
import logging
import azure.functions as func
import uuid
import os
import json
from urllib.parse import urlparse
from azure.storage.blob import BlobServiceClient
from PyPDF2 import PdfReader
from docx import Document
import openai
import time 
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient

app = func.FunctionApp()

# Initialize Azure Search client once
search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
search_api_key = os.getenv("AZURE_SEARCH_API_KEY")
index_name = os.getenv("AZURE_SEARCH_INDEX_NAME")

search_client = SearchClient(
    endpoint=search_endpoint,
    index_name=index_name,
    credential=AzureKeyCredential(search_api_key)
)

@app.function_name(name="ServiceBusMessageListener")
@app.service_bus_queue_trigger(
    arg_name="msg",
    queue_name="testqueue",  # replace with your queue name
    connection="AZURE_SERVICE_BUS_CONNECTION_STRING"
)

def service_bus_queue_listener(msg: func.ServiceBusMessage):
    try:
        message_body = msg.get_body().decode('utf-8')
        logging.info(f"Received message from Service Bus Queue: {message_body}")
        body = json.loads(message_body)
        file_url = body.get("file_url")
        if not file_url:
            raise ValueError("Missing file_url in message.")

        documents = download_chunk_and_vectorize_file(file_url)
        logging.info(f"Prepared {len(documents)} documents for upload.")

        if documents:
            logging.info("Waiting 8 minutes before uploading to Azure AI Search...")
            time.sleep(8 * 60)  # Wait 6 minutes (360 seconds)
            upload_vectors_to_search(documents)
            logging.info("Upload to Azure Search completed.")
        else:
            logging.warning("No documents to upload.")

    except Exception as e:
        logging.error(f"Error processing message: {e}")



def download_chunk_and_vectorize_file(file_url: str):
    try:
        parsed = urlparse(file_url)
        path_parts = parsed.path.lstrip("/").split("/", 1)
        if len(path_parts) != 2:
            raise ValueError("Invalid blob URL format.")

        container_name, blob_name = path_parts
        file_name = os.path.basename(blob_name)
        logging.info(f"Container: {container_name}, Blob: {blob_name}")
        extension = os.path.splitext(blob_name)[1].lower()
        blob_service_client = BlobServiceClient.from_connection_string(os.getenv("AZURE_STORAGE_CONNECTION_STRING"))
        blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)

        blob_data = blob_client.download_blob().readall()
        logging.info(f"Downloaded blob: {blob_name}, size: {len(blob_data)} bytes")

        # Parse and chunk content
        if extension == ".pdf":
            reader = PdfReader(io.BytesIO(blob_data))
            text = "\n".join([page.extract_text() or "" for page in reader.pages])
        elif extension == ".docx":
            doc = Document(io.BytesIO(blob_data))
            text = "\n".join([para.text for para in doc.paragraphs])
        elif extension == ".txt":
            text = blob_data.decode("utf-8")
        else:
            raise ValueError(f"Unsupported file type: {extension}")

        # Chunk the text
        chunks = [text[i:i+500] for i in range(0, len(text), 500)]
        logging.info(f"Total chunks created: {len(chunks)}")

        openai.api_key = os.getenv("OPENAI_API_KEY")


        documents = []
        for idx, chunk in enumerate(chunks):
            try:
                response = openai.embeddings.create(
                    model="text-embedding-3-small",  # or text-embedding-ada-002
                    input=chunk
                )
                vector = response.data[0].embedding
                doc = {
                    "id": str(uuid.uuid4()),
                    "content": chunk,
                    "contentVector": vector,
                    "fileName": file_name 
                }
                documents.append(doc)
                logging.info(f"Embedded and prepared document {idx+1}/{len(chunks)}")
            except Exception as embed_error:
                logging.error(f"Failed to embed chunk {idx+1}: {embed_error}")

        return documents

    except Exception as e:
        logging.error(f"Failed to download and chunk file from URL: {file_url}, Error: {e}")
        return []

def upload_vectors_to_search(documents):
    try:
        result = search_client.upload_documents(documents)
        logging.info(f"Upload result: {result}")
    except Exception as e:
        logging.error(f"Error uploading documents to Azure Search: {e}")