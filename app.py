import streamlit as st
import torch
from web3 import Web3
import json
from pathlib import Path

# -----------------------------
# Load secrets
# -----------------------------
RPC_URL = st.secrets["blockchain"]["RPC_URL"]
PRIVATE_KEY = st.secrets["blockchain"]["PRIVATE_KEY"]
CONTRACT_ADDRESS = st.secrets["blockchain"]["CONTRACT_ADDRESS"]

# -----------------------------
# Web3 Setup
# -----------------------------
w3 = Web3(Web3.HTTPProvider(RPC_URL))
account = w3.eth.account.from_key(PRIVATE_KEY)

# -----------------------------
# Load Contract ABI
# -----------------------------
ABI_FILE = Path("contract_abi.json")
if ABI_FILE.exists():
    contract_abi = json.load(open(ABI_FILE))
    contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=contract_abi)
else:
    contract = None

# -----------------------------
# Load YOLO Model
# -----------------------------
@st.cache_resource
def load_model():
    return torch.hub.load("ultralytics/yolov5", "custom", path="yolov8n.pt")

model = load_model()

# -----------------------------
# Streamlit UI
# -----------------------------
st.title("🐄 LivestockMon – AI Livestock Tracker + NFT Ownership")

st.write("Upload a livestock image for AI detection and minting.")

uploaded = st.file_uploader("Upload Image", type=["jpg", "png", "jpeg"])

if uploaded:
    st.image(uploaded, caption="Uploaded Image", use_column_width=True)

    # Run YOLO on image
    with open("temp.jpg", "wb") as f:
        f.write(uploaded.getvalue())

    results = model("temp.jpg")
    st.image(results.render()[0], caption="AI Detection")

    st.success("Detection complete!")

    # -----------------------------
    # Mint NFT Button
    # -----------------------------
    if st.button("Mint NFT on Blockchain"):

        if contract is None:
            st.error("Contract ABI missing. Upload contract_abi.json.")
        else:
            try:
                # Prepare transaction
                tx = contract.functions.mintLivestockNFT(
                    account.address,
                    "ipfs://sampleCIDofImage"
                ).build_transaction({
                    "from": account.address,
                    "nonce": w3.eth.get_transaction_count(account.address),
                    "gas": 400000,
                    "gasPrice": w3.eth.gas_price
                })

                # Sign
                signed_tx = w3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY)

                # Send
                tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
                st.success(f"NFT Minted! Transaction Hash: {tx_hash.hex()}")

            except Exception as e:
                st.error(f"Error minting NFT: {str(e)}")


st.info("Private keys are securely stored using Streamlit Secrets (not in app.py).")
