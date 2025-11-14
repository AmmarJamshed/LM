import streamlit as st
from web3 import Web3
import json
import requests

st.title("🔍 Verify Livestock NFT")

RPC_URL = st.secrets["blockchain"]["RPC_URL"]
CONTRACT_ADDRESS = st.secrets["blockchain"]["CONTRACT_ADDRESS"]
ABI = json.loads(st.secrets["contract"]["ABI"])

web3 = Web3(Web3.HTTPProvider(RPC_URL))
contract = web3.eth.contract(address=Web3.to_checksum_address(CONTRACT_ADDRESS), abi=ABI)

token_id = st.number_input("Enter Token ID", min_value=0)

if st.button("Check NFT"):
    try:
        token_uri = contract.functions.tokenURI(token_id).call()
        metadata = requests.get(token_uri).json()

        st.success("NFT Found!")
        st.json(metadata)
        st.image(metadata["image"])

    except:
        st.error("Token does not exist.")
