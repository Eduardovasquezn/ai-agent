from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


# Define your request models here
class MessageRequestType(BaseModel):
    request_type: Literal[
        "track_packages", "update_users_data", "shipping_guidance", "lost_packages"
    ] = Field(description="Type of message requested by the user")
    confidence_score: float = Field(
        description="Confidence score of the update request, ranging from 0 to 1."
    )
    description: str = Field(
        description="A cleaned and structured description of the update request."
    )


class TrackingPackageRequest(BaseModel):
    """Router LLM call: Determine the tracking package request"""

    tracking_code: str = Field(description="Extract the tracking code.")
    confidence_score: float = Field(
        description="Confidence score of the update request, ranging from 0 to 1."
    )
    description: str = Field(
        description="A cleaned and structured description of the update request."
    )


class UserProfileUpdateRequest(BaseModel):
    """Schema for updating user profile information"""

    field_type: Literal["address", "city"] = Field(
        description="The specific user profile field type to update."
    )
    field_value: str = Field(
        description="The specific user profile field value to update."
    )
    confidence_score: float = Field(
        description="Confidence score of the update request, ranging from 0 to 1."
    )
    description: str = Field(
        description="A cleaned and structured description of the update request."
    )


class PolicyCategoryRequest(BaseModel):
    """Classifies the user's query into the appropriate policy category."""

    request_type: Literal["lost_packages", "shipping_information"] = Field(
        description="Category of policy the user is asking about."
    )
    confidence_score: float = Field(
        description="Confidence score for category classification, ranging from 0 to 1."
    )
    answer: str = Field(description="The answer to the user's question.")


class SearchQdrantRequest(BaseModel):
    """Represents the request structure for searching Qdrant."""

    user_input: str = Field(description="The user's question about company policy.")
    collection_name: Literal["lost_package_policy", "shipping_information"] = Field(
        description="The Qdrant collection to search in."
    )
    confidence_score: float = Field(
        description="Confidence score for category classification, ranging from 0 to 1."
    )

    model_config = ConfigDict(extra="forbid")  # Ensures no extra properties are allowed


# Define request model
class UserMessage(BaseModel):
    message: str
