import logging
import uuid
from datetime import datetime
from typing import Any, Dict

from qdrant_client import QdrantClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from src.config import settings
from src.utils.custom_logging import setup_logging

# Set up logging system
setup_logging()


def get_db_session():
    """
    Initializes a database connection and returns a session factory.

    Returns:
        sessionmaker: A session factory bound to the database engine.
    """
    interactions_db_url = f"{settings.database_url}/postal_service"
    engine = create_engine(interactions_db_url)
    return sessionmaker(bind=engine)


def get_interactions_from_db(limit: int = 5):
    """
    Retrieve the last `limit` user interactions with the LLM from the database.

    Args:
        limit (int): Number of recent interactions to fetch. Default is 5.

    Returns:
        list: A list of tuples containing (question, response) from user interactions.
    """
    try:
        logging.info("Get the database session.")
        SessionLocal = get_db_session()

        query = text(
            """
            SELECT question, response
            FROM user_llm_interactions
            ORDER BY interaction_time DESC
            LIMIT :limit;
            """
        )

        # Open a new session
        with SessionLocal() as session:
            result = session.execute(query, {"limit": limit}).fetchall()
            interactions = [(row[0], row[1]) for row in result]

        logging.info(f"Retrieved {len(interactions)} interactions from the database.")
        return interactions

    except Exception as error:
        logging.error(f"Error retrieving interactions: {error}", exc_info=True)
        return []


def save_interaction_to_db(question: str, response: str):
    """
    Saves a user interaction (question & response) into the PostgreSQL database.

    Args:
        question (str): User's input question.
        response (str): LLM's generated response.

    Returns:
        bool: True if the interaction is successfully saved, False otherwise.
    """
    try:
        logging.info("Get the database session.")
        SessionLocal = get_db_session()

        interaction_id = uuid.uuid4()  # Generate a unique ID

        query = text(
            """
            INSERT INTO user_llm_interactions (id, question, response, interaction_time)
            VALUES (:id, :question, :response, :interaction_time);
        """
        )

        # Use a context manager for session handling
        with SessionLocal() as session:
            session.execute(
                query,
                {
                    "id": interaction_id,
                    "question": question,
                    "response": response,
                    "interaction_time": datetime.now(),
                },
            )
            session.commit()  # Commit transaction

        logging.info("User interaction saved successfully.")
        return True

    except Exception as error:
        logging.error(f"Error saving interaction: {error}")
        return False


def get_latest_tracking_info(tracking_code: str):
    """
    Retrieve the latest tracking information for a given tracking code.

    Args:
        tracking_code (str): The package tracking code.
        session (Session, optional): An existing SQLAlchemy session. If None, a new session is created.

    Returns:
        dict or None: Tracking information if found, otherwise None.
    """
    logging.info("Fetching tracking information for: %s", tracking_code)

    query = text(
        """
        SELECT last_update, location, status, shipping_type
        FROM package_tracking
        WHERE tracking_code = :tracking_code
        ORDER BY last_update DESC
        LIMIT 1
    """
    )

    SessionLocal = get_db_session()

    # Use a context manager for session handling
    with SessionLocal() as session:
        result = session.execute(query, {"tracking_code": tracking_code}).fetchone()

    if result:
        last_update, location, status, shipping_type = result
        return {
            "last_update": last_update,
            "location": location,
            "status": status,
            "shipping_type": shipping_type,
        }
    else:
        return None  # No record found


def query_to_update_users_data(user_id: uuid.UUID, reason: str, value_to_update: str):
    """Update user data in the database.

    Args:
        user_id (uuid.UUID): The unique identifier of the user.
        reason (str): The field to update ('address' or 'city').
        value_to_update (str): The new value to set.
        session (Session): The active database session.

    Raises:
        ValueError: If the reason is not valid.
    """

    # Validate user_id
    try:
        user_id = uuid.UUID(str(user_id))
    except ValueError:
        logging.error("Invalid user_id format.")
        raise ValueError("Invalid UUID format for user_id.")

    # Define allowed update fields
    allowed_fields = {"address", "city"}

    if reason not in allowed_fields:
        logging.error(f"Invalid update reason: {reason}")
        raise ValueError(f"Invalid reason '{reason}'. Allowed values: {allowed_fields}")

    # Dynamic SQL query
    query = text(
        f"UPDATE users SET {reason} = :value_to_update WHERE user_id = :user_id;"
    )

    try:
        SessionLocal = get_db_session()

        # Use a context manager for session handling
        with SessionLocal() as session:
            session.execute(
                query, {"user_id": user_id, "value_to_update": value_to_update}
            )

            session.commit()

        logging.info(
            f"Successfully updated {reason} for user {user_id} to '{value_to_update}'."
        )

    except Exception as e:
        session.rollback()
        logging.error(
            f"Failed to update {reason} for user {user_id}: {e}", exc_info=True
        )
        raise


def search_qdrant(
    user_input: str,
    embedding_model: Any,
    collection_name: str = "shipping_information",
    limit: int = 3,
) -> Dict[str, str]:
    """
    Searches a Qdrant vector store for relevant company policies.

    Args:
        user_input (str): The user's query.
        collection_name (str): The name of the Qdrant collection to search.
        embedding_model: The embedding model used to encode the query.
        client_connection: The Qdrant client connection.
        limit (int, optional): The maximum number of results to retrieve. Default is 3.

    Returns:
        dict: A dictionary containing the retrieved policy text or a message if no results are found.
    """
    logging.info("Connecting to Qdrant...")
    client_connection = QdrantClient(
        url=settings.qdrant.url,
    )

    logging.info(
        f"Searching Qdrant collection '{collection_name}' for query: {user_input}"
    )

    try:
        query_vector = embedding_model.encode(user_input).tolist()

        search_results = client_connection.search(
            collection_name=collection_name, query_vector=query_vector, limit=limit
        )

        if not search_results:
            logging.warning("No relevant company policies found.")
            return {"answer": "No relevant company policies found."}

        policy_texts = [
            result.payload.get("text", "No text available")
            for result in search_results[:2]
        ]
        response = {"answer": "\n\n".join(policy_texts)}

        logging.info("Successfully retrieved policy information from Qdrant.")
        return response

    except Exception as e:
        logging.error(f"Error occurred while searching Qdrant: {e}", exc_info=True)
        return {"answer": "An error occurred while retrieving company policies."}
