# Main handler
import logging

from src.core import (
    process_tracking_package_request,
    retrieve_policy_and_shipping_info,
    route_message_request,
    update_user_profile,
)


def llm_router(user_message):
    """
    Handles user requests by classifying the intent and routing it
    to the appropriate function.

    Args:
        user_message (str): The message sent by the user.

    Returns:
        str: Response from the appropriate function or an error message.
    """
    try:
        # Step 1: Classify the user's intent
        classify_message = route_message_request(user_message)
        intent = classify_message.request_type

        # Step 2: Route the request based on the classified intent
        if intent == "track_packages":
            # Extract tracking code from message
            tracking_code = process_tracking_package_request(user_message)

            return tracking_code

        elif intent == "update_users_data":
            update_data = update_user_profile(user_message)

            return update_data

        elif intent in ["shipping_guidance", "lost_packages"]:

            vdb_response = retrieve_policy_and_shipping_info(user_message)

            return vdb_response.choices[0].message.parsed.answer
        else:
            return "I'm unable to process that request. Can you provide more details?"

    except Exception as e:
        # Log the error and return a user-friendly response
        logging.error(f"Error handling request: {e}")
        return (
            "An error occurred while processing your request. Please try again later."
        )


# question1 = "What should I do if my package is lost?"
# print(llm_router(question1))
# question2 = "How long does it take to send a package to Economy International? And the price?"
# print(llm_router(question2))
# question3 = "I want to track the location of my package"
# print(llm_router(question3))
