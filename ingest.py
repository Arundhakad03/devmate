from pathlib import Path
from git import Repo
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter, Language

REPOS_DIR = Path("data/repos")



def clone_repo(repo_url:str) -> Path:
    url = repo_url.strip()

    if url.endswith("/"):
        url = url[:-1]

    if url.endswith(".git"):
        url = url[:-4]

    parts = url.split("/")
    repo_name = parts[-1]

    save_path = REPOS_DIR / repo_name

    if save_path.exists():
        print("repo already downloaded" , save_path)
        return save_path

    REPOS_DIR.mkdir(parents=True, exist_ok=True)
    print("cloning....", repo_url)
    Repo.clone_from(repo_url,save_path, depth=1)

    return save_path




# if __name__ == "__main__":
#     path = clone_repo("https://github.com/Arundhakad03/TripMate")
#     print(path)

    
SKIP_DIRS = [".git", "node_modules", "venv", ".venv", "__pycache__", "dist", "build"]
ALLOWED_EXTS = [".py", ".js", ".ts", ".java", ".md"]


def load_files(repo_path : Path) -> list[Document]:
    docs = []

    for file in repo_path.rglob("*"):
        if not file.is_file():
            continue

        short_path = file.relative_to(repo_path)

        if any(folder in SKIP_DIRS for folder in short_path.parts):
            continue

        if file.suffix not in ALLOWED_EXTS:
            continue

        try:
            text = file.read_text(encoding="utf-8")

        except (UnicodeDecodeError, OSError):
            continue

        doc = Document(
            page_content= text,
            metadata={"file_path" : str (short_path), "language" : file.suffix},

        )


        docs.append(doc)

    return docs




# if __name__ == "__main__":
#     path = clone_repo("https://github.com/Arundhakad03/TripMate")
#     docs = load_files(path)
#     print(len(docs), "files loaded")
#     print(docs[0].metadata)




def chunk_files(docs:list[Document]) -> list[Document]:
    chunks = []

    for doc in docs:
        ext = doc.metadata["language"]

        if ext == ".py":
            spliter = RecursiveCharacterTextSplitter.from_language(
                language=Language.PYTHON,
                chunk_size=800,
                chunk_overlap=100,
            )


        elif ext in (".js",".ts"):
            spliter = RecursiveCharacterTextSplitter.from_language(
                language=Language.JS,
                chunk_size= 800,
                chunk_overlap=100,
            )

        else :
            spliter = RecursiveCharacterTextSplitter(
                chunk_size=800,
                chunk_overlap=100,
            )

        pieces = spliter.split_text(doc.page_content)

        char_count = 0

        for piece in pieces:
            start_line = doc.page_content[:char_count].count("\n") +1
            end_line = start_line + piece.count("\n")

            chunk_doc = Document(
                page_content=piece,
                metadata= {
                    "file_path": doc.metadata["file_path"],
                    "start_line":start_line,
                    "end_line":end_line,
                }
            )
            chunks.append(chunk_doc)
            char_count += len(piece)

    return chunks



# if __name__ == "__main__":
#     path = clone_repo("https://github.com/Arundhakad03/TripMate")
#     docs = load_files(path)
#     chunks = chunk_files(docs)
#     print(len(docs), "files ->", len(chunks), "chunks")
#     print(chunks[0].page_content[:200])
#     print(chunks[0].metadata)




