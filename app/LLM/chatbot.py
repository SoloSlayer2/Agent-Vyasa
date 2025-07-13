from langchain.prompts import ChatPromptTemplate
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda, RunnableSerializable
from langchain_ollama import ChatOllama
from Schemas.schemas import Message, State


class Chatbot_Init:
    def __init__(self):
        self.model = ChatOllama(model="mistral:latest", temperature=0.2)
        self.rag_prompt = ChatPromptTemplate.from_template(
            "Use the following docs to answer the query.\n\nDocs:\n{docs}\n\nQuery: {query}"
        )
        self.parser = StrOutputParser()
        self.system_prompt1 = """You are Agent Vyāsa, a calm and insightful assistant.
Respond with clarity and understanding, drawing on your training and any prior context provided.
Begin the conversation naturally. No need for introductions unless asked.
"""
        self.system_prompt2 = """You are Vyāsa — a helpful, clear, and concise assistant.

You have access to a short-term memory of previous conversations with the user. 
Use this memory to better understand the current question and respond with relevance and clarity.

Your role is to provide accurate, well-structured answers. 
If the question is ambiguous, ask for clarification.

Keep your responses polite and focused.

When possible:
- Summarize complex ideas simply.
- Avoid unnecessary repetition.
- Maintain a professional yet friendly tone.

Do not hallucinate facts.  
If you're unsure, respond honestly that you don't know.
"""
        self.system_prompt3 = """You are an AI assistant designed to perform two key tasks with high accuracy:
1. **Summarize**: Condense the given context into a clear, concise summary while preserving key information.
2. **Answer Perfectly**: Provide accurate, complete, and well-structured answers to user queries using the provided context.  

### Instructions:
- **For Summarization**:
  - Extract the most important details from the context.
  - Keep the summary short yet informative (2-3 sentences unless specified otherwise).
  - Maintain neutrality and avoid introducing new information.

- **For Answers**:
  - Respond **directly** to the query without deviation.
  - Ground your answer **strictly in the provided context**. Do not hallucinate.
  - If the context is insufficient, say: "I don't have enough information to answer this."

### Output Format:
- Use clear, bullet points or short paragraphs for readability.
- Always prioritize **accuracy** over verbosity."""

    def chatbot(self, state: State):
        """Last state message should always be human"""
        if len(state["messages"]) == 1:
            msgs = [
                SystemMessage(content=self.system_prompt1),
                HumanMessage(content=state["messages"][-1].content),
            ]
        else:
            msgs = [SystemMessage(content=self.system_prompt2)]

            hist = state["messages"][-20:]

            for msg in hist:
                if msg.role == "human":
                    msgs.append(HumanMessage(content=msg.content))
                elif msg.role == "ai":
                    msgs.append(AIMessage(content=msg.content))

        if not state[
            "context"
        ]:  # The control is coming from the user or you didnt get the context
            msgs = ChatPromptTemplate.from_messages(msgs)
            chain = msgs | self.model | self.parser
            content = chain.invoke({})
            state["messages"].append(Message(role="ai", content=content))

        else:  # The control is coming from Tathya
            prompt = ChatPromptTemplate.from_messages(
                [self.system_prompt3, self.rag_prompt]
            )

            chain = prompt | self.model | self.parser
            content = chain.invoke({"docs": state["context"], "query": state["query"]})

            state["context"] = None
            state["query"] = None
            state["messages"].append(Message(role="ai", content=content))
