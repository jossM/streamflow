# streamflow aws infrastructure terraform module
This folder is a terraform module that creates all of streamflow infrastructure elements.

It requires the following providers to work:
1. AWS provider (to deploy the dynamodb tables)
2. Helm provider (to deploy the api service)
3. Serverless provider (to deploy the api scheduler function)