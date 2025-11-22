try:
    from langchain.embeddings import OpenAIEmbeddings
    print('OK: imported OpenAIEmbeddings from langchain.embeddings')
except Exception as e:
    print('ERROR:', type(e).__name__, e)
    try:
        from langchain_openai import OpenAIEmbeddings
        print('OK: imported OpenAIEmbeddings from langchain_openai')
    except Exception as e2:
        print('ALT ERROR:', type(e2).__name__, e2)
