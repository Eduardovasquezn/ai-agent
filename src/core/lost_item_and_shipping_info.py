import json
import logging
from typing import Any

from langfuse.decorators import observe
from sentence_transformers import SentenceTransformer

from src.config import settings
from src.schemas import PolicyCategoryRequest, SearchQdrantRequest
from src.utils import (
    get_interactions_from_db,
    get_langfuse_client,
    get_openai_client,
    save_interaction_to_db,
    search_qdrant,
)

# Access the clients
openai_client = get_openai_client()
langfuse_client = get_langfuse_client()


# Define the function
@observe()
def retrieve_policy_and_shipping_info(
    user_input: str, client: Any = openai_client, model_name: str = settings.MODEL_NAME
) -> PolicyCategoryRequest:
    """
    Retrieves a company policy answer based on the user's question.

    Args:
        user_input: User's input question about company policy.
        client: OpenAI API client.
        model: LLM model to use.

    Returns:
        str: Final formatted policy answer.
    """

    # Define tools for function calling
    tools = [
        {
            "type": "function",
            "function": {
                "name": "search_qdrant",
                "description": "Retrieve company policy from the correct Qdrant collection based on the user's query.",
                "parameters": SearchQdrantRequest.model_json_schema(),
                "strict": True,  # Enforce strict validation
            },
        }
    ]

    # Retrieve last 5 interactions from the database
    interactions = get_interactions_from_db()

    # Initial Messages
    messages = [
        {
            "role": "system",
            "content": "You are a helpful assistant that strictly follows company policies.",
        },
        {
            "role": "system",
            "content": "These are the last five messages of previous conversation but You do not need to use these pieces of information if not relevant:\n"
            + "\n".join(
                [
                    f"User: {interaction[0]}\nAssistant: {interaction[1]}"
                    for interaction in interactions
                ]
            )
            + "\n\n(End of previous conversation)",
        },
        {"role": "user", "content": f"Current conversation: {user_input}"},
    ]

    # Call LLM to determine the right tool call
    logging.info("Route message based on the vector store db information")
    completion = client.chat.completions.create(
        model=model_name, messages=messages, tools=tools
    )
    completion_tools = completion.choices[0].message.tool_calls

    if completion_tools:
        embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL)
        # Process tool calls
        for tool_call in completion.choices[0].message.tool_calls:
            tool_args = json.loads(tool_call.function.arguments)
            tool_args.pop("confidence_score", None)

            # Create a new ChatCompletionMessage and convert it to a dictionary before appending
            messages.append(
                {
                    "content": None,
                    "refusal": None,
                    "role": "assistant",
                    "audio": None,
                    "function_call": None,
                    "tool_calls": [
                        tool_call.model_dump()
                    ],  # Convert tool_call to a dictionary
                    "annotations": [],
                }
            )

            # Retrieve policy from Qdrant
            response = search_qdrant(**tool_args, embedding_model=embedding_model)

            # Append retrieved policy to messages
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(response),
                }
            )

            # Ask LLM to generate a refined response
            messages.append(
                {
                    "role": "system",
                    "content": (
                        "Based on the extracted company policy, generate a **clear and concise answer** "
                        "to the user's question."
                    ),
                }
            )

    # Generate final completion with refined answer
    final_completion = client.beta.chat.completions.parse(
        model=model_name, messages=messages, response_format=PolicyCategoryRequest
    )

    save_interaction_to_db(
        question=user_input, response=final_completion.choices[0].message.parsed.answer
    )

    return final_completion


# Example Usage:
# input_question = "What should I do if my package is lost?"
# input_question_2 = "How long does it take to send a package to Economy International? And the price?"
# policy_answer = retrieve_policy_and_shipping_info(user_input=input_question)
