from llms.lmstudio_llms import LmstudioLLM

if __name__ == "__main__":
    # Example usage
    lmstudio_llm = LmstudioLLM()
    prompt = "What is the capital of France?"
    response = lmstudio_llm._call(prompt)
    print(response)
