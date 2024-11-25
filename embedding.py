#built-in modules
import os
import json
import io 

#third-party libraries
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient, ContainerClient, BlobBlock, BlobClient, StandardBlobTier
from sentence_transformers import SentenceTransformer
import torch


def generate_embeddings(client, data_source: list[str], embedding_model="text-embedding-3-small", batch_size=1000):
    """
    Generates embeddings for a list of queries using the specified model and batch size.

    Args:
        client: The API client used to make the embedding requests.
        data_source: List of strings for which embeddings will be generated.
        embedding_model: The model used to generate the embeddings (default is "text-embedding-3-small").
        batch_size: The number of queries processed in each batch (default is 1000).

    Returns:
        List of generated embeddings.
    """

    embeddings = []
    for batch_start in range(0, len(data_source), batch_size):
        batch_end = batch_start + batch_size
        batch = data_source[batch_start:batch_end]
        print(f"Processing Batch {batch_start} to {batch_end-1}")
        response = client.embeddings.create(model=embedding_model, input=batch)

        # Double check embeddings are in the same order as input
        for i, be in enumerate(response.data):
            assert i == be.index

        # Extract embeddings and add to the list
        batch_embeddings = [e.embedding for e in response.data]
        embeddings.extend(batch_embeddings)

    return embeddings

def load_data(path: str):
    with open(path, 'r', encoding='utf-8') as file:
        return json.load(file)

def save_data(data, output_path):
    # output_path = os.path.join("..", "..", "..", "data", "docVectors-e5.json")
    with open(output_path, "w") as f:
        json.dump(data, f)


def download_blob_content(account_url, container_name, blob_name):
    """
    Downloads the content of a blob from Azure Blob Storage.
    
    Args:
        account_url (str): The URL of the Azure storage account.
        container_name (str): The name of the container where the blob resides.
        blob_name (str): The name of the blob to download.
    
    Returns:
        bytes: The content of the blob as a bytes object.
    """
    try:
        # Initialize the credential and BlobServiceClient
        credential = DefaultAzureCredential()
        blob_service_client = BlobServiceClient(account_url, credential=credential)
        
        # Get the blob client
        blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
        
        # Download and return the blob content
        blob_content = blob_client.download_blob().readall()
        return blob_content

    except Exception as e:
        print(f"An error occurred: {e}")
        return None


def parse_blob_content_to_json(blob_content):
    """
    Parses a bytes object containing JSON data into a Python dictionary.
    
    Args:
        blob_content (bytes): The content of the blob as a bytes object.
    
    Returns:
        dict: The parsed JSON data as a Python dictionary.
    """
    try:
        # Create a file-like object from the bytes
        data = io.BytesIO(blob_content)
        
        # Load and return JSON data
        json_data = json.load(data)
        return json_data

    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


def populate_embeddings(data_source: list[dict], model_name: str, key: str='text', batch_size: int=1000):
    """
    Populates the initial JSON object with embeddings generated through the previous function.

    Args:
        data_source (list[dict]): A list of dictionaries containing the data for which embeddings will be generated.
        model_name (str): The Hugging Face model used to generate the embeddings.
        key (str, optional): The key in the dictionaries whose corresponding values will be used for generating embeddings. Defaults to 'text'.
        batch_size (int, optional): The number of items processed in each batch. Defaults to 1000.

    Returns:
        list[dict]: The updated data source with embeddings.
    """
    embeddings = generate_embeddings_huggingface(data_source, model_name, key, batch_size)
    for i, embedding in enumerate(embeddings):
        data_source[i]['embedding'] = embedding
    return data_source


def generate_embeddings_huggingface(data_source: list[dict], model_name: str, key: str='text', batch_size: int=1000):
    """
    Generates embeddings for a list of dictionaries using a specified Hugging Face model and batch size.
    Args:
        data_source (list[dict]): A list of dictionaries containing the data for which embeddings will be generated.
        model_name (SentenceTransformer): The Hugging Face model used to generate the embeddings.
        key (str, optional): The key in the dictionaries whose corresponding values will be used for generating embeddings. Defaults to 'text'.
        batch_size (int, optional): The number of items processed in each batch. Defaults to 1000.
        list: A list of generated embeddings. If an error occurs during processing, None is returned for the corresponding batch.

    Returns:
        List of generated embeddings.
    """
    #Initialize the model 
    model = SentenceTransformer(model_name, model_kwargs={"torch_dtype": torch.float16})

    #Extract the values corresponding to the specified key
    extracted_texts = [elem[key] for elem in data_source if key in elem]

    #store embeddings
    embeddings = []

    #Process in batches
    for batch_start in range(0, len(data_source), batch_size):
        batch_end = batch_start + batch_size
        batch = extracted_texts[batch_start:batch_end]
        print(f"Processing Batch {batch_start} to {batch_end-1}")
        try:
          response = model.encode(batch)
          batch_embeddings = response.tolist()
          embeddings.extend(batch_embeddings)
        except:
          embeddings.extend([None] * batch_size)
        #   pending_indices.extend(range(batch_start, batch_end))
          print('------',  range(batch_start, batch_end))
        finally:
            #free GPU memory if applicable
            torch.cuda.empty_cache()

    return embeddings


def upload_blob_content(data: json, account_url: str, container_name: str, blob_name: str):
    """
    Downloads the content of a blob from Azure Blob Storage.
    
    Args:
        account_url (str): The URL of the Azure storage account.
        container_name (str): The name of the container where the blob resides.
        blob_name (str): The name of the blob to download.
    
    Returns:
        bytes: The content of the blob as a bytes object.
    """
    try:
        # Initialize the credential and BlobServiceClient
        credential = DefaultAzureCredential()
        blob_service_client = BlobServiceClient(account_url, credential=credential)

        # Get the client for the container
        container_client = blob_service_client.get_container_client(container=container_name)

        # Upload  the blob content
        container_client.upload_blob(name=blob_name, data=data, overwrite=True)
        

    except Exception as e:
        print(f"An error occurred: {e}")
        return None


def main0():
    # This model supports two prompts: "s2p_query" and "s2s_query" for sentence-to-passage and sentence-to-sentence tasks, respectively.
    # They are defined in `config_sentence_transformers.json`
    query_prompt_name = "s2p_query"
    queries = [
        "What are some ways to reduce stress?",
        "What are the benefits of drinking green tea?",
    ]
    # docs do not need any prompts
    docs = [
        "There are many effective ways to reduce stress. Some common techniques include deep breathing, meditation, and physical activity. Engaging in hobbies, spending time in nature, and connecting with loved ones can also help alleviate stress. Additionally, setting boundaries, practicing self-care, and learning to say no can prevent stress from building up.",
        "Green tea has been consumed for centuries and is known for its potential health benefits. It contains antioxidants that may help protect the body against damage caused by free radicals. Regular consumption of green tea has been associated with improved heart health, enhanced cognitive function, and a reduced risk of certain types of cancer. The polyphenols in green tea may also have anti-inflammatory and weight loss properties.",
    ]

    # ！The default dimension is 1024, if you need other dimensions, please clone the model and modify `modules.json` to replace `2_Dense_1024` with another dimension, e.g. `2_Dense_256` or `2_Dense_8192` !
    # on gpu
    model = SentenceTransformer("dunzhang/stella_en_400M_v5", trust_remote_code=True).cuda()
    # you can also use this model without the features of `use_memory_efficient_attention` and `unpad_inputs`. It can be worked in CPU.
    # model = SentenceTransformer(
    #     "dunzhang/stella_en_400M_v5",
    #     trust_remote_code=True,
    #     device="cpu",
    #     config_kwargs={"use_memory_efficient_attention": False, "unpad_inputs": False}
    # )
    query_embeddings = model.encode(queries, prompt_name=query_prompt_name)
    doc_embeddings = model.encode(docs)
    print(query_embeddings.shape, doc_embeddings.shape)
    # (2, 1024) (2, 1024)

    similarities = model.similarity(query_embeddings, doc_embeddings)
    print(similarities)
    # tensor([[0.8398, 0.2990],
    #         [0.3282, 0.8095]])


def main1():
    data = load_data(r"C:\Users\Andres.DESKTOP-D77KM25\OneDrive - Stanford\Laboral\Lawgorithm\Corte Constitucional\processed_files\json\jurisprudencia_2023_muestra.json")
    data = populate_embeddings(data_source=data,
                        model_name="BAAI/bge-multilingual-gemma2",
                        key='text',
                        batch_size=1000)   
    save_data(data, r'C:\Users\Andres.DESKTOP-D77KM25\OneDrive - Stanford\Laboral\Lawgorithm\Corte Constitucional\processed_files\embeddings\embeddings_2023.json')

    
def main2():
    pass
    # data = get_blob_storage_file(connection_string= , 
    #                              container_name=, 
    #                              blob_name=)
    # data = populate_embeddings(data_source=data,
    #                     model_name="BAAI/bge-multilingual-gemma2",
    #                     key='text',
    #                     batch_size=1000)
    # save_data_blog_storage(data)


def main3():
    # TODO: Replace <storage-account-name> with your actual storage account name
    account_url = "https://lawgorithm.blob.core.windows.net"
    credential = DefaultAzureCredential()

    # Create the BlobServiceClient object
    blob_service_client = BlobServiceClient(account_url, credential=credential)

    blob_client = blob_service_client.get_blob_client(container='jurisprudencia-chunked-text',
                                                    blob= 'jurisprudencia_2023_muestra.json')
    # Download the blob content
    blob_content = blob_client.download_blob().readall()

    # print(blob_content)
    
    data = io.BytesIO(blob_content)
    json_data = json.load(data)
    for elem in json_data:
        print(elem[''])


def main4():
    data = download_blob_content(account_url="https://lawgorithm.blob.core.windows.net", 
                          container_name='jurisprudencia-chunked-text', 
                          blob_name='jurisprudencia_2023_muestra.json')
    print('1')
    data=parse_blob_content_to_json(data)
    print('2')
    data=populate_embeddings(data_source=data, 
                            model_name="BAAI/bge-multilingual-gemma2",
                            key='text',
                            batch_size=1000)
    print('3')
    for elem in data:
        print(elem.keys())
    upload_blob_content(data,
                        account_url="https://lawgorithm.blob.core.windows.net",
                        container_name='jurisprudencia-embeddings', 
                        blob_name='prueba')

    

if __name__ == "__main__":
    main4()
