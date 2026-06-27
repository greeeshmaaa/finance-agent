import os
from dotenv import load_dotenv
from plaid.api import plaid_api
from plaid import Configuration, ApiClient
from plaid.model.sandbox_public_token_create_request import SandboxPublicTokenCreateRequest
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.products import Products

load_dotenv()

# Point the client at Plaid's sandbox environment
configuration = Configuration(
    host="https://sandbox.plaid.com",
    api_key={
        "clientId": os.environ["PLAID_CLIENT_ID"],
        "secret": os.environ["PLAID_SECRET"],
    },
)
client = plaid_api.PlaidApi(ApiClient(configuration))


def create_access_token():
    # 1. Create a sandbox public token for a fake institution.
    #    'ins_109508' is Plaid's standard sandbox test bank.
    pt_request = SandboxPublicTokenCreateRequest(
        institution_id="ins_109508",
        initial_products=[Products("transactions")],
    )
    pt_response = client.sandbox_public_token_create(pt_request)
    public_token = pt_response.public_token

    # 2. Exchange the public token for a permanent access token.
    exchange_request = ItemPublicTokenExchangeRequest(public_token=public_token)
    exchange_response = client.item_public_token_exchange(exchange_request)
    access_token = exchange_response.access_token

    return access_token


if __name__ == "__main__":
    token = create_access_token()
    print("ACCESS TOKEN:")
    print(token)
    print("\nAdd this to your .env as PLAID_ACCESS_TOKEN")
