from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from dotenv import load_dotenv
load_dotenv()

from store import repo_key


def get_llm():
    return ChatGroq(
        model="openai/gpt-oss-120b",
        temperature=0,
        )



prompt = ChatPromptTemplate.from_template(
    """ tum ek helpful code assistant ho. Neeche diye gaye context se hi sawal ka jawab do.
    Agar context me jawab nhi mile, toh sidha boldo ki "mujhe iska jawab coontext mein nhi mila."
    Kabhi bhi khud se guess mat karna.
    context:{context}
    sawaal:{question}

"""
)




def ask(db, question:str, repo:str | None = None) -> dict:
    # repo diya ho to sirf usi repo ke chunks me search karo
    filt = {"repo": repo_key(repo)} if repo else None
    results = db.similarity_search(question, k=4, filter=filt)

    context = "\n\n".join(r.page_content for r in results)

    llm = get_llm()
    chain = prompt | llm | StrOutputParser()
    response = chain.invoke({"context":context, "question": question})

    sources = [
        {
            "file":r.metadata["file_path"],
            "start_line":r.metadata["start_line"],
            "end_line":r.metadata["end_line"]
        }
        for r in results
    ]
    return {"response": response, "sources": sources}



if __name__ == "__main__":
    from ingest import clone_repo, load_files, chunk_files
    from store import save_to_store

    path = clone_repo("https://github.com/Arundhakad03/TripMate")
    docs = load_files(path)
    chunks = chunk_files(docs)
    db = save_to_store(chunks, repo_name=path.name)

    result = ask(db, "flight search kaise hoti hai is project mein?", repo=path.name)
    print("ANSWER:", result["response"])
    print("SOURCES:", result["sources"])