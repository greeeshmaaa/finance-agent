import os, json
from dotenv import load_dotenv
from plaid.api import plaid_api
from plaid import Configuration, ApiClient
from plaid.model.sandbox_public_token_create_request import SandboxPublicTokenCreateRequest
from plaid.model.sandbox_public_token_create_request_options import SandboxPublicTokenCreateRequestOptions
from plaid.model.products import Products

load_dotenv()
configuration = Configuration(
    host="https://sandbox.plaid.com",
    api_key={"clientId": os.environ["PLAID_CLIENT_ID"], "secret": os.environ["PLAID_SECRET"]},
)
client = plaid_api.PlaidApi(ApiClient(configuration))

# Minimal documented example — just two transactions
config = {
    "override_accounts": [{
        "type": "depository",
        "subtype": "checking",
        "transactions": [
            {"date_transacted": "2026-06-01", "date_posted": "2026-06-02",
             "currency": "USD", "amount": 15.49, "description": "Netflix"},
        ],
    }]
}

options = SandboxPublicTokenCreateRequestOptions(
    override_username="user_custom",
    override_password=json.dumps(config),
)
request = SandboxPublicTokenCreateRequest(
    institution_id="ins_109508",
    initial_products=[Products("transactions")],
    options=options,
)
resp = client.sandbox_public_token_create(request)
print("SUCCESS:", resp.public_token)
