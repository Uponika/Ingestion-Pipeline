import os
import openai
import requests

openai.api_key = os.getenv("OPENAI_API_KEY")

AZURE_SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
AZURE_SEARCH_API_KEY = os.getenv("AZURE_SEARCH_API_KEY")
AZURE_SEARCH_INDEX = os.getenv("AZURE_SEARCH_INDEX_NAME")


def retrieve_answer_from_index(query: str, top_k: int = 5) -> str:
    try:
        # Step 1: Embed the query using OpenAI
        embedding_response = openai.embeddings.create(
            input=query,
            model="text-embedding-3-small"
        )
        query_vector = embedding_response.data[0].embedding

        # Step 2: Construct vector search REST API request
        search_url = f"{AZURE_SEARCH_ENDPOINT}/indexes/{AZURE_SEARCH_INDEX}/docs/search?api-version=2023-11-01"

        headers = {
            "Content-Type": "application/json",
            "api-key": AZURE_SEARCH_API_KEY
        }


        body = {
            "vectorQueries": [
                {
                    "kind": "vector",
                    "vector": query_vector,
                    "fields": "contentVector",
                    "k": top_k
                }
            ],
            "select": "content,fileName"
        }

        response = requests.post(search_url, headers=headers, json=body)
        response.raise_for_status()

        results = response.json().get("value", [])

        if not results:
            return "Sorry, no relevant information was found."

        # Step 3: Build context from retrieved chunks
        context = ""
        for item in results:
            context += f"[{item['fileName']}]: {item['content']}\n---\n"

        # Step 4: Use OpenAI chat completion with the context
        chat_response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant. Answer based only on the context below."},
                {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"}
            ],
            temperature=0.3
        )

        return chat_response.choices[0].message.content.strip()

    except Exception as e:
        return f"Error occurred: {e}"

# test the function using a sample query