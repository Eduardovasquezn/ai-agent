import logging
from typing import Any

from langfuse.decorators import observe

from src.config import settings
from src.schemas import TrackingPackageRequest
from src.utils import (
    get_interactions_from_db,
    get_langfuse_client,
    get_latest_tracking_info,
    get_openai_client,
    save_interaction_to_db,
)

# Access the clients
openai_client = get_openai_client()
langfuse_client = get_langfuse_client()


@observe()
def process_tracking_package_request(
    user_input: str, client: Any = openai_client, model_name: str = settings.MODEL_NAME
) -> str:
    """Process and track package requests using LLM and database queries.

    Args:
        user_input (str): User's query containing tracking information.
        client (Any): OpenAI client for LLM interaction.
        model_name (str): Model name for LLM processing.
    Returns:
        str: A formatted tracking response message or an error message.
    """

    logging.info("Processing tracking request.")

    # Retrieve last 5 interactions from the database
    interactions = get_interactions_from_db()

    try:
        # Step 1: Use LLM to extract tracking number
        completion = client.beta.chat.completions.parse(
            model=model_name,
            messages=[
                {
                    "role": "system",
                    "content": "Extract the tracking number. It must start with PKG.",
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
            response_format=TrackingPackageRequest,
        )

        result = completion.choices[0].message.parsed

        tracking_code = result.tracking_code
        logging.info(f"Extracted Tracking Code: {tracking_code}")

        # Step 2: Fetch the latest tracking info from the database
        output_query = get_latest_tracking_info(tracking_code)

        # Step 3: Save tracking request for logging purposes
        save_interaction_to_db(question=user_input, response=result.description)

        # Step 4: Return formatted response based on tracking results
        if output_query:
            response = f"""
            📦 **Package Tracking Details** 📦

            🕒 **Last Update:** {output_query['last_update']}
            🚀 **Status:** {output_query['status']}
            📍 **Location:** {output_query['location']}
            📦 **Shipping Type:** {output_query['shipping_type']}

            🔍 Check back for real-time updates!
            """
        else:
            response = """
            ❌ **Tracking Error** ❌

            ⚠️ The tracking code you entered does not exist or has no updates available.
            Please double-check the code and try again.
            """

        logging.info("Tracking response generated successfully.")
        return response

    except Exception as e:
        logging.error(f"Error processing tracking request: {e}", exc_info=True)
        return (
            "⚠️ An error occurred while processing your request. Please try again later."
        )


# Call function with defined model name
# response = process_tracking_package_request(user_input="PKG100256")
# print(response)
