import logging
from typing import Any

from langfuse.decorators import observe

from src.config import settings
from src.schemas import UserProfileUpdateRequest
from src.utils import (
    get_interactions_from_db,
    get_langfuse_client,
    get_openai_client,
    query_to_update_users_data,
    save_interaction_to_db,
)

# Access the clients
openai_client = get_openai_client()
langfuse_client = get_langfuse_client()


@observe()
def update_user_profile(
    user_input: str,
    client: Any = openai_client,
    model_name: str = settings.MODEL_NAME,
    user_id: str = "06cecdbd-ac6b-45f5-84f7-c6a8631a4ed6",
) -> UserProfileUpdateRequest:
    """
    Processes a user profile update request using an LLM.

    Args:
        client: LLM client for making API calls.
        model_name (str): The model name to use for parsing.
        user_input (str): User's request describing the update.
        user_id (str): The unique identifier of the user.

    Returns:
        UserProfileUpdateRequest or None if parsing fails.
    """

    logging.info(f"Routing message request for user {user_id}")

    try:

        # Retrieve last 5 interactions from the database
        interactions = get_interactions_from_db()

        completion = client.beta.chat.completions.parse(
            model=model_name,
            messages=[
                {
                    "role": "system",
                    "content": "Extract the field type the user would like to update.",
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
            ],
            response_format=UserProfileUpdateRequest,
        )

        result = completion.choices[0].message.parsed
        logging.info(f"Extracted update request: {result}")

    except Exception as e:
        logging.error(
            f"Failed to parse LLM response for user {user_id}: {e}", exc_info=True
        )
        return None

    try:
        query_to_update_users_data(
            user_id=user_id,
            reason=result.field_type,
            value_to_update=result.field_value,
        )
        logging.info(f"Successfully updated user {user_id}'s profile.")

        save_interaction_to_db(question=user_input, response=result.description)
    except Exception as e:
        logging.error(f"Database update failed for user {user_id}: {e}", exc_info=True)
        return None

    return result
