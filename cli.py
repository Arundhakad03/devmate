import typer
from ingest import clone_repo, load_files,chunk_files
from store import save_to_store, get_embeddings, list_indexed_repos
from RAG import ask
from langchain_chroma import Chroma


app = typer.Typer()
PERSIST_DIR = "data/chroma"

@app.command()
def index(repo_url : str):
    "repo ka clone and chunks vector store me save karna"
    path = clone_repo(repo_url)
    docs = load_files(path)
    chunks = chunk_files(docs)
    save_to_store(chunks, repo_name=path.name, persist_dir=PERSIST_DIR)
    print(f"indexed {len(chunks)} chunks from {repo_url}")


@app.command()
def ask_question(question : str, repo : str = typer.Option(None, help="kis repo me search karna hai (jaise TripMate)")):
    "indexed repo se question karne ke liye"
    embeddings = get_embeddings()
    db = Chroma(persist_directory=PERSIST_DIR, embedding_function=embeddings)
    result = ask(db, question, repo=repo)
    print("\nANSWER : \n", result['response'])
    print("\n SOURCES : ")
    for s in result['sources']:
        print(f"{s['file']} (line {s['start_line']} - {s['end_line']})")


@app.command()
def repos():
    "kaun kaun se repos index hain"
    found = list_indexed_repos(PERSIST_DIR)
    if not found:
        print("koi repo index nhi hai")
    for r in found:
        print(r)



if __name__ == "__main__":
    app()