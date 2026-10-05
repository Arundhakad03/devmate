from dotenv import load_dotenv
load_dotenv()

from langchain_core.tools import tool
from langchain_groq import ChatGroq
from langgraph.prebuilt import create_react_agent

from agent import (
    search_code,
    indexed_repos,
    get_issue,
    list_similar_issues,
    comment_on_pr,
    triage_issue,
)

SYSTEM_PROMPT = """Tum DevMate ho, ek developer assistant chatbot.
- Code ke sawaal ke liye search_code tool use karo. User ne repo bataya ho to repo parameter me do.
- Kaun se repos index hain, ye indexed_repos se pata karo.
- GitHub issue dekhne ke liye get_issue, milte-julte issues ke liye list_similar_issues,
  aur issue triage ke liye triage_github_issue use karo.
- Comment post karne ke liye post_comment use karo (wo user se khud confirm karta hai).
- User jis bhasha me baat kare, usi me jawab do.
- Kabhi guess mat karo. Tool se jawab na mile to saaf bolo.
"""

MAX_HISTORY = 20  # last 20 messages yaad rakhega


@tool
def triage_github_issue(repo_full_name: str, issue_number: int) -> str:
    "GitHub issue ko triage karo: label, priority, reasoning aur similar issues. repo_full_name format: 'owner/repo'"
    r = triage_issue(repo_full_name, issue_number)
    return (
        f"Label: {r.label}\n"
        f"Priority: {r.priority}\n"
        f"Reasoning: {r.reasoning}\n"
        f"Similar: {', '.join(r.similar_issues) or 'none'}"
    )


@tool
def post_comment(repo_full_name: str, number: int, comment: str) -> str:
    "GitHub issue ya PR pe comment post karo. Post karne se pehle user se terminal me confirmation leta hai."
    print(f"\n  [confirm] {repo_full_name} #{number} pe ye comment post hoga:\n  ---\n  {comment}\n  ---")
    ok = input("  Post karna hai? (y/n): ").strip().lower()
    if ok != "y":
        return "User ne comment cancel kar diya. Kuch post nahi hua."
    return comment_on_pr.invoke(
        {"repo_full_name": repo_full_name, "pr_number": number, "comment": comment}
    )


def build_agent():
    llm = ChatGroq(model="openai/gpt-oss-120b", temperature=0)
    tools = [
        search_code,
        indexed_repos,
        get_issue,
        list_similar_issues,
        triage_github_issue,
        post_comment,
    ]
    return create_react_agent(llm, tools)


def main():
    agent = build_agent()
    history = []  # sirf user aur final assistant messages

    print("DevMate ready. 'exit' se band karo, '/clear' se history saaf karo.")

    while True:
        try:
            q = input("\nyou> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nbye!")
            break

        if not q:
            continue
        if q.lower() in {"exit", "quit"}:
            print("bye!")
            break
        if q == "/clear":
            history.clear()
            print("history clear ho gayi.")
            continue

        messages = [("system", SYSTEM_PROMPT)] + history[-MAX_HISTORY:] + [("user", q)]

        try:
            state = agent.invoke({"messages": messages})
        except Exception as e:
            print(f"Error: {e}")
            continue

        # kaun sa tool use hua, wo dikhao
        for m in state["messages"][len(messages):]:
            for call in getattr(m, "tool_calls", None) or []:
                print(f"  [tool] {call['name']}({call['args']})")

        answer = state["messages"][-1].content
        print(f"\ndevmate> {answer}")

        history += [("user", q), ("assistant", answer)]


if __name__ == "__main__":
    main()
