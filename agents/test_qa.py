from agents.qa.qa_agent import QAAgent

agent = QAAgent()

questions = [
    "Where is authentication implemented?",
    "How does login work?",
    "Where are API requests configured?",
    "What happens when a user is unauthorized?",
    "Where are routes defined?",
    "How is state management handled?",
    "Where are forms implemented?",
    "How are API errors handled?",
    "Where is user authorization checked?",
    "How does the application start?"
]


agent = QAAgent()


for q in questions:

    print("\n====================")
    print("QUESTION:", q)

    result = agent.answer(q)

    print("\nANSWER:")
    print(result["answer"])