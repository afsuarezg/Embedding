from sentence_transformers import SentenceTransformer


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


def generate_embeddings_huggingface(data_source: list[str], model: SentenceTransformer, batch_size=1000):
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
        try:
          response = model.encode(batch)
          batch_embeddings = response.tolist()
          embeddings.extend(batch_embeddings)
        except:
          embeddings.extend([None] * batch_size)

        torch.cuda.empty_cache()
        # if batch_start == 1000:
        #   break
    return embeddings


def generate_embeddings_huggingface(data_source: list[str], model: SentenceTransformer, batch_size=1000):
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
    pending_indices = []
    embeddings = []
    for batch_start in range(0, len(data_source), batch_size):
        batch_end = batch_start + batch_size
        batch = data_source[batch_start:batch_end]
        print(f"Processing Batch {batch_start} to {batch_end-1}")
        try:
          response = model.encode(batch)
          batch_embeddings = response.tolist()
          embeddings.extend(batch_embeddings)
        except:
          embeddings.extend([None] * batch_size)
          pending_indices.extend(range(batch_start, batch_end))
          print('------',  range(batch_start, batch_end))

        torch.cuda.empty_cache()
        # if batch_start == 1000:
        #   break

    return embeddings, pending_indices


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


if __name__ == "__main__":
    pass