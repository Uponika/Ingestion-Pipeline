#Step 1: HTTP Trigger Function to Upload Files to Azure Blob Storage
# This function handles file uploads via HTTP requests and stores them in Azure Blob Storage.
# Ensure you have the necessary packages installed and your Azure Storage connection string set up.

# import azure.functions as func
# import logging
# import os
# from azure.storage.blob import BlobServiceClient
# from io import BytesIO

# def main(req: func.HttpRequest) -> func.HttpResponse:
#     logging.info("File upload request received.")

#     try:
#         # Get file from multipart/form-data
#         files = req.files.get("file")
#         if not files:
#             return func.HttpResponse("No file found in request.", status_code=400)

#         file_name = files.filename
#         file_stream = BytesIO(files.stream.read())

#         # Upload to Blob Storage
#         connection_string = os.environ["AZURE_STORAGE_CONNECTION_STRING"]
#         container_name = "uploaded-files"  # ensure this exists in your storage account

#         blob_service_client = BlobServiceClient.from_connection_string(connection_string)
#         blob_client = blob_service_client.get_blob_client(container=container_name, blob=file_name)
#         blob_client.upload_blob(file_stream, overwrite=True)

#         return func.HttpResponse(f"File '{file_name}' uploaded successfully.", status_code=200)

#     except Exception as e:
#         logging.exception("File upload failed.")
#         return func.HttpResponse(f"Upload failed: {str(e)}", status_code=500)


# Step 2: Enhanced Function to Upload Files and Send Metadata to Azure Service Bus
# This function uploads files to Azure Blob Storage and sends metadata to an Azure Service Bus queue.
import azure.functions as func
import logging
import os
import uuid
import json
from azure.storage.blob import BlobServiceClient
from azure.servicebus import ServiceBusClient, ServiceBusMessage
from io import BytesIO

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("File upload request received.")

    try:
        # Extract uploaded file
        files = req.files.get("file")
        if not files:
            return func.HttpResponse("No file found in request.", status_code=400)

        file_name = files.filename
        file_stream = BytesIO(files.stream.read())

        # Upload to Azure Blob Storage
        connection_string = os.environ["AZURE_STORAGE_CONNECTION_STRING"]
        container_name = "uploaded-files"

        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        blob_client = blob_service_client.get_blob_client(container=container_name, blob=file_name)
        blob_client.upload_blob(file_stream, overwrite=True)

        # Generate metadata
        blob_url = blob_client.url
        file_id = str(uuid.uuid4())
        message_payload = {
            "file_url": blob_url,
            "file_name": file_name,
            "file_id": file_id
        }

        # Send to Azure Service Bus
        servicebus_connection_str = os.environ["AZURE_SERVICE_BUS_CONNECTION_STRING"]
        queue_name = os.environ.get("AZURE_SERVICE_BUS_QUEUE_NAME", "file-upload-events")

        sb_client = ServiceBusClient.from_connection_string(servicebus_connection_str)
        with sb_client:
            sender = sb_client.get_queue_sender(queue_name)
            with sender:
                message = ServiceBusMessage(json.dumps(message_payload))
                sender.send_messages(message)

        return func.HttpResponse(f"File '{file_name}' uploaded and message sent.", status_code=200)

    except Exception as e:
        logging.exception("Error during file upload or messaging.")
        return func.HttpResponse(f"Upload failed: {str(e)}", status_code=500)
