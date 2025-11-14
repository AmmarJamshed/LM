import streamlit as st
from web3 import Web3
from solcx import compile_standard, install_solc
import json
import base64
import os

st.set_page_config(page_title="LivestockMon", layout="wide")

# -------------------------------
# PWA injection
# -------------------------------
def inject_pwa():
    st.markdown(
        """
        <link rel="manifest" href="/static/manifest.json" />
        <script>
            if ("serviceWorker" in navigator) {
                navigator.serviceWorker.register("/static/service-worker.js");
            }
        </script>
        """,
        unsafe_allow_html=True,
    )

inject_pwa()

# -------------------------------
# Blockchain Setup
# -------------------------------
install_solc("0.8.20")

with open("LivestockOwnershipNFT.sol", "r") as f:
    contract_source = f.read()

compiled = compile_standard(
    {
        "language": "Solidity",
        "sources": {"LivestockOwnershipNFT.sol": {"content": contract_source}},
        "settings": {"outputSelection": {"*": {"*": ["abi", "evm.bytecode"]}}},
    },
    solc_version="0.8.20",
)

abi = compiled["contracts"]["LivestockOwnershipNFT.sol"]["LivestockOwnershipNFT"]["abi"]
bytecode = compiled["contracts"]["LivestockOwnershipNFT.sol"]["LivestockOwnershipNFT"]["evm"]["bytecode"]["object"]

st.title("🐄 LivestockMon – Blockchain Livestock Ownership")

rpc = st.text_input("Enter RPC URL (Polygon Amoy / Anryton / Hardhat):")
pk = st.text_input("Private Key:", type="password")

if rpc and pk:
    w3 = Web3(Web3.HTTPProvider(rpc))
    acct = w3.eth.account.from_key(pk)

    st.success(f"Connected: {acct.address}")

    if st.button("Deploy Contract"):
        Contract = w3.eth.contract(abi=abi, bytecode=bytecode)

        tx = Contract.constructor().build_transaction({
            "from": acct.address,
            "nonce": w3.eth.get_transaction_count(acct.address),
            "gas": 3000000,
            "gasPrice": w3.eth.gas_price,
        })

        signed = acct.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)

        st.write("⏳ Deploying...")
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

        st.success(f"Contract deployed at {tx_receipt.contractAddress}")
        st.session_state["contract"] = tx_receipt.contractAddress

if "contract" in st.session_state:
    st.subheader("Mint Livestock NFT")

    metadata = st.text_area("Livestock metadata (JSON or text):")

    if metadata and st.button("Mint NFT"):
        contract = w3.eth.contract(address=st.session_state["contract"], abi=abi)

        tx = contract.functions.mint(metadata).build_transaction({
            "from": acct.address,
            "nonce": w3.eth.get_transaction_count(acct.address),
            "gas": 3000000,
            "gasPrice": w3.eth.gas_price,
        })

        signed = acct.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)

        st.success(f"Tx sent: {tx_hash.hex()}")
