from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings


def get_embeddings():
    return OllamaEmbeddings(
        model="nomic-embed-text"
    )


def repo_key(name: str) -> str:
    "'owner/repo' ya 'repo' dono se same key banao"
    return name.strip().rstrip("/").split("/")[-1].lower()


def save_to_store(chunks, repo_name: str, persist_dir="data/chroma"):
    key = repo_key(repo_name)

    # har chunk pe repo ka naam save karo
    for c in chunks:
        c.metadata["repo"] = key

    embeddings = get_embeddings()
    db = Chroma(persist_directory=persist_dir, embedding_function=embeddings)

    # re-index karne pe is repo ke purane chunks hata do (duplicates na bane)
    db._collection.delete(where={"repo": key})

    # batch me add karo taaki bade repo pe limit na toote
    for i in range(0, len(chunks), 100):
        db.add_documents(chunks[i:i + 100])

    return db


def list_indexed_repos(persist_dir="data/chroma") -> list[str]:
    embeddings = get_embeddings()
    db = Chroma(persist_directory=persist_dir, embedding_function=embeddings)
    metas = db.get(include=["metadatas"])["metadatas"]
    return sorted({m["repo"] for m in metas if m and "repo" in m})


if __name__ == "__main__":
    from ingest import clone_repo, load_files, chunk_files

    path = clone_repo("https://github.com/Arundhakad03/TripMate")
    docs = load_files(path)
    chunks = chunk_files(docs)

    db = save_to_store(chunks, repo_name=path.name)
    print("Saved", len(chunks), "chunks to Chroma")

    results = db.similarity_search(
        "flight search kaise hoti hai", k=3, filter={"repo": repo_key(path.name)}
    )
    for r in results:
        print(r.metadata["file_path"], "->", r.page_content[:100])