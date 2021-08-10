import pytest
from typing import Dict

from model.pagination import serialize_token, deserialize_token, DynamoPageToken


@pytest.fixture
def no_filter_page_token():
    return DynamoPageToken(start_key={
        'string': {
            'S': 'string',
            'N': 'string',
            'SS': [
                'string',
            ],
            'NS': [
                'string',
            ],
            'NULL': True,
            'BOOL': False
        }
    })


def test_serialization(no_filter_page_token: DynamoPageToken):
    assert no_filter_page_token == deserialize_token(serialize_token(no_filter_page_token))
