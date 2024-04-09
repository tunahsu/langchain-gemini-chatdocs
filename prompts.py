# flake8: noqa
from langchain_core.prompts.prompt import PromptTemplate
from langchain.output_parsers import StructuredOutputParser, ResponseSchema


# Define a schema for the text response.
text_schema = ResponseSchema(
    name="text",
    description="""
        Your detailed response to a user's question in the user's preferred language.
        IMPORTANT: The preferred language can be found in the content of the User Inquiry.
    """
)

# Define a schema for the picture response.
picture_schema = ResponseSchema(
    name="picture",
    description="""
        Provide a Python Dictionary with alternate texts as keys and their respective image URLs as values.
        IMPORTANT: You cannot provide image URLs you do not see in the Documents.
        IMPORTANT: Provide a single string "NO_PICTURE" instead of Python Dictionary if no image URL is provided.
        """
)
response_schema = [text_schema, picture_schema]
output_parser = StructuredOutputParser.from_response_schemas(response_schema)
FORMAT_INSTRUCTIONS = output_parser.get_format_instructions()

qa_template = """
    Hey! You are a friendly and intelligent AI assistant, \
    utilizing your vast knowledge base and summarization capabilities \
    to provide assistance to users based on the context of documents and to answer their queries in detail.
    \n
    {context}
    \n
    Question: {question}
    \n
    Format Instructions: {format_instructions}
"""

QA_PROMPT = PromptTemplate(
    template=qa_template,
    input_variables=['context', 'question'],
    partial_variables={'format_instructions': FORMAT_INSTRUCTIONS}
)
