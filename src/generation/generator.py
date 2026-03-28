from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq

from src.generation.prompt import ANSWER_TEMPLATE, SYSTEM_PROMPT
from src.utils.config import MODEL_NAME


class AnswerGenerator:
    def __init__(self) -> None:
        self.llm = ChatGroq(model=MODEL_NAME, temperature=0)
        self.prompt = ChatPromptTemplate.from_messages(
            [
                ('system', SYSTEM_PROMPT),
                ('human', ANSWER_TEMPLATE),
            ]
        )
        self.chain = self.prompt | self.llm | StrOutputParser()

    def generate(self, question: str, context: str) -> str:
        return self.chain.invoke({'question': question, 'context': context}).strip()