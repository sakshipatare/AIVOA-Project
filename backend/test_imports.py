try:
    import fastapi
    import sqlalchemy
    import langchain
    import langgraph
    import langchain_groq
    print("All imports successful!")
except Exception as e:
    print(f"Import failed: {e}")
