from typing import List
from pydantic import BaseModel, Field


class UserInput(BaseModel):
    identifier: str = Field(
        default="",
        description=(
            "Identifier: can be a customer ID (numeric), "
            "email address (contains @), or phone number (starts with + or contains digits). "
            "Return empty string if no identifier is found in the message."
        ),
    )


class UserProfile(BaseModel):
    customer_id: str = Field(description="The customer ID of the customer")
    music_preferences: List[str] = Field(
        default_factory=list,
        description="The music preferences of the customer (artists, genres, albums they like)",
    )
