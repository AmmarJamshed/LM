import streamlit as st
from web3 import Web3
import json
import time
import os
from ultralytics import YOLO
import base64
import requests

st.set_page_config(page_title="LivestockMon", layout="wide")

# -------------------
# Load secrets
# -------------------
RPC_URL = st.secrets["blockchain"]["RPC_URL"]
PRIVATE_KEY = st.secrets["blockchain"]["PRIVATE_KEY"]
CONTRACT_ADDRESS = st.secrets["blockchain"]["CONTRACT_ADDRESS"]
ABI = json.loads(st.secrets["contract"]["ABI"])

# -------------------
# Setup blockchain
# -------------------
web3 = Web3(Web3.HTTPProvider(RPC_URL))
account = web3.eth.account.from_key(PRIVATE_KEY)
contract = web3.eth.contract(address=Web3.to_checksum_address(CONTRACT_ADDRESS), abi=ABI)

# -------------------
# Load YOLO Model
# -------------------
model = YOLO("yolov8n.pt")

# -------------------
# Helper: Upload file to IPFS (Web3Storage)
# -------------------
W3S_TOKEN = "https://api.web3.storage/upload"
# If you have a real token, set secrets["ipfs"]["W3S"] = "KEY"

def upload_to_ipfs(file_bytes, file_name):
    headers = {
        "Authorization": f"Bearer {st.secrets['ipfs']['W3S']}",
    }
    files = {
        "file": (file_name, file_bytes)
    }
    response = requests.post(W3S_TOKEN, headers=headers, files=files)

    cid = response.json()["cid"]
    return f"https://{cid}.ipfs.w3s.link/{file_name}"

# -------------------
# UI
# -------------------
st.title("🐄 LivestockMon — AI Livestock NFT Identity")

uploaded_image = st.file_uploader("Upload a livestock image", type=["jpg", "png", "jpeg"])

if uploaded_image:

    st.image(uploaded_image, caption="Uploaded Image", use_column_width=True)

    # YOLO prediction
    with st.spinner("Detecting livestock..."):
        results = model.predict(uploaded_image.getvalue())
        boxes = results[0].boxes

    if len(boxes) == 0:
        st.error("❌ No livestock detected.")
        st.stop()

    st.success(f"Detected {len(boxes)} animal(s).")

    # Upload image to IPFS
    with st.spinner("Uploading image to IPFS..."):
        image_ipfs = upload_to_ipfs(uploaded_image.getvalue(), uploaded_image.name)

    # Build metadata
    metadata = {
        "name": "Livestock Passport NFT",
        "description": "Certified on-chain livestock identity",
        "image": image_ipfs,
    }

    metadata_bytes = json.dumps(metadata).encode()
    meta_ipfs = upload_to_ipfs(metadata_bytes, "metadata.json")

    st.success("Metadata uploaded to IPFS!")
    st.json(metadata)

    # Mint NFT
    if st.button("Mint NFT"):
        with st.spinner("Minting NFT on blockchain..."):
            nonce = web3.eth.get_transaction_count(account.address)

            txn = contract.functions.mintLivestockNFT(
                account.address,
                meta_ipfs
            ).build_transaction({
                "from": account.address,
                "nonce": nonce,
                "gas": 500000,
                "gasPrice": web3.to_wei("2", "gwei"),
            })

            signed_txn = web3.eth.account.sign_transaction(txn, private_key=PRIVATE_KEY)
            tx_hash = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
            receipt = web3.eth.wait_for_transaction_receipt(tx_hash)

        st.success("NFT Minted Successfully!")
        st.write("Transaction Hash:", tx_hash.hex())
        st.write("Metadata:", meta_ipfs)
