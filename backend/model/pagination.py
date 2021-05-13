from base64 import b64encode, b64decode
from binascii import Error as Base64Error
from pydantic import BaseModel, Field
import json
from typing import Dict


class DynamoPageToken(BaseModel):
    start_key: Dict[str, Dict] = Field(
        title="Start Key",
        description="Dynamo start key to get the next value.",
        default_factory=dict)
    filters: str = Field(
        title="Query Filter expression",
        description="Filters applied to dynamo records.",
        default="")


def serialize_token(token: DynamoPageToken) -> str:
    """Converts page information into a simple token string that can be used for pagination"""
    json_data = json.dumps(token.dict(), sort_keys=True)
    token_bytes = b64encode(json_data.encode('ascii'))
    return token_bytes.decode('ascii')


def deserialize_token(token: str) -> DynamoPageToken:
    """
    Converts a token into information necessary to get the next page
    :raise ValueError: in case the token can not be transformed into a PageToken object
    """
    token_bytes = token.encode('ascii')
    try:
        json_data = json.loads(b64decode(token_bytes, validate=True))
        return DynamoPageToken(**json_data)
    except (json.JSONDecodeError, Base64Error, TypeError) as e:
        raise ValueError(f"Failed to parse token into a PageToken: {e}")
