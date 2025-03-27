import logging
from typing import Any

from langfuse.decorators import observe

from src.config import settings
from src.schemas import MessageRequestType
from src.utils import (
    get_interactions_from_db,
    get_langfuse_client,
    get_openai_client,
    save_interaction_to_db,
)

# Access the clients
openai_client = get_openai_client()
langfuse_client = get_langfuse_client()


@observe()
def route_message_request(
    user_input: str, client: Any = openai_client, model_name: str = settings.MODEL_NAME
) -> MessageRequestType:
    """
    Routes the message request to the appropriate LLM endpoint to determine the type of request.

    This function takes the user's input, processes it with historical interactions from the database,
    and sends the relevant context to the LLM. It then parses the LLM's response and routes the message accordingly.

    Args:
        client (Any): The LLM client to make the request.
        model_name (str): The name of the model to be used for processing.
        user_input (str): The current user's input message.

    Returns:
        MessageRequestType: A Pydantic model containing the request type, confidence score, and description.
    """
    """Router LLM call to determine the type of request with memory"""
    logging.info("Routing message request with memory")

    # Retrieve last 5 interactions from DB
    interactions = get_interactions_from_db()

    # Prepare messages with history + the current user input
    messages = [
        {
            "role": "system",
            "content": "Determine if this is a request to track_packages, change_user_data, shipping_guidance, lost_packages.",
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

    # Call the LLM to get a response
    logging.info("Calling the LLM...")
    completion = client.beta.chat.completions.parse(
        model=model_name,
        messages=messages,
        response_format=MessageRequestType,
    )

    # Parse the result
    result = completion.choices[0].message.parsed
    logging.info(
        f"Request routed as: {result.request_type} with confidence: {result.confidence_score}"
    )

    # Save the new interaction to the DB (with the LLM's response)
    save_interaction_to_db(question=user_input, response=result.description)

    return result
