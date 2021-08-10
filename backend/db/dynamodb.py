import boto3

import config

dynamodb = boto3.resource("dynamodb") if not config.TEST_ENV else None
