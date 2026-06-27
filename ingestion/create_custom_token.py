import os
import json
from dotenv import load_dotenv
from plaid.api import plaid_api
from plaid import Configuration, ApiClient
from plaid.model.sandbox_public_token_create_request import SandboxPublicTokenCreateRequest
from plaid.model.sandbox_public_token_create_request_options import SandboxPublicTokenCreateRequestOptions
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.products import Products

from ingestion.custom_seed import override

load_dotenv()

configuration = Configuration(
    host="https://sandbox.plaid.com",
    api_key={
        "clientId": os.environ["PLAID_CLIENT_ID"],
        "secret": os.environ["PLAID_SECRET"],
    },
)
client = plaid_api.PlaidApi(ApiClient(configuration))


def create_custom_access_token():
    # Pass our custom dataset via the override_username/password mechanism.
    # Plaid sandbox reads the custom config from a special 'user_custom' login.
    options = SandboxPublicTokenCreateRequestOptions(
        override_username="user_custom",
        override_password=json.dumps(override),
    )
    pt_request = SandboxPublicTokenCreateRequest(
        institution_id="ins_109508",
        initial_products=[Products("transactions")],
        options=options,
    )
    pt_response = client.sandbox_public_token_create(pt_request)
    public_token = pt_response.public_token

    exchange_request = ItemPublicTokenExchangeRequest(public_token=public_token)
    exchange_response = client.item_public_token_exchange(exchange_request)
    return exchange_response.access_token


if __name__ == "__main__":
    token = create_custom_access_token()
    print("CUSTOM ACCESS TOKEN:")
    print(token)
