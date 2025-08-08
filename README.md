
# Azure-Based Ingestion Pipeline for RAG Applications

This repository provides an end-to-end ingestion pipeline using **Azure Services**, designed to prepare and index documents for use in a Retrieval-Augmented Generation (RAG) application. It includes components for file upload, message queueing, embedding generation, and indexing in **Azure AI Search**.

---


---

## Components

### 1. FileUploadFunctionApp
- Uploads files to Azure Blob Storage.
- Sends a message to Azure Service Bus Queue with metadata and Blob URL.

### 2. ServiceBusListener
- Triggered by messages in the Service Bus Queue.
- Downloads the file, chunks it, generates OpenAI embeddings, and indexes it in Azure AI Search.

### 3. chat_completion.py
- A utility script to query your AI Search Index and retrieve relevant chunks via REST API.

---

## Prerequisites

- Azure Subscription with:
  - Blob Storage
  - Service Bus
  - Azure OpenAI access
  - Azure AI Search
- Python 3.9+
- Azure CLI installed and authenticated
- [Azure Functions Core Tools](https://learn.microsoft.com/en-us/azure/azure-functions/functions-run-local)

---

## Setup Instructions

### 1. Clone the Repository

- git clone https://github.com/your-username/azure-ingestion-pipeline.git
- cd azure-ingestion-pipeline

### 2. Installation of packages for both the directories

- pip install -r requirements.txt

### 3. Set Environment Variables
     
- BLOB_STORAGE_CONNECTION_STRING=your_blob_storage_conn_string
- BLOB_CONTAINER_NAME=your_container_name

- SERVICE_BUS_CONNECTION_STRING=your_service_bus_conn_string
- SERVICE_BUS_QUEUE_NAME=your_queue_name

- AZURE_OPENAI_API_KEY=your_openai_key
- AZURE_OPENAI_ENDPOINT=https://your-openai-instance.openai.azure.com/
- AZURE_OPENAI_EMBEDDING_MODEL=text-embedding-ada-002

- AZURE_SEARCH_ENDPOINT=https://your-search-instance.search.windows.net/
- AZURE_SEARCH_API_KEY=your_search_key
- AZURE_SEARCH_INDEX_NAME=your_index_name

### 4. Deploying to Azure

For each app:

- cd FileUploadFunctionApp  # or ServiceBusListener
- func azure functionapp publish <your-function-app-name> 

### 5. Uploading a File

Call the HTTP trigger of FileUploadFunctionApp:

- curl -X POST "https://<your-function-app-name>.azurewebsites.net/api/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@./sample.pdf"

### 6. Local Testing

To test locally using Azure Functions Core Tools:

#### Start FileUploadFunctionApp locally

- cd FileUploadFunctionApp
- func start

#### Upload a file via local endpoint

- curl -X POST http://localhost:7071/api/upload \
  -H "Content-Type: multipart/form-data" \
  -F "file=@./your-document.pdf"

### 7. Cleanup Resources

To remove all Azure resources (use with caution):
- az group delete --name <your-resource-group> --yes --no-wait