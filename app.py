import streamlit as st
import requests
import base64
from web3 import Web3
from PIL import Image
import io
import json

st.set_page_config(page_title="LivestockMon", layout="wide")

st.title("🐮 LivestockMon — Cloud Livestock Detection + NFT Minting")

# ---------------------------
# Load Blockchain Secrets
# ---------------------------
RPC_URL = st.secrets["blockchain"]["RPC_URL"]
PRIVATE_KEY = st.secrets["blockchain"]["PRIVATE_KEY"]
CONTRACT_ADDRESS = st.secrets["blockchain"]["CONTRACT_ADDRESS"]
ABI = json.loads(st.secrets["blockchain"]["ABI"])
ROBOFLOW_API = st.secrets["blockchain"]["ROBOFLOW_API"]

# Blockchain setup
w3 = Web3(Web3.HTTPProvider(RPC_URL))
account = w3.eth.account.from_key(PRIVATE_KEY)
contract = w3.eth.contract(address=Web3.to_checksum_address(CONTRACT_ADDRESS), abi=ABI)

# ---------------------------
# Upload Image
# ---------------------------
uploaded = st.file_uploader("Upload livestock image...", type=["jpg", "jpeg", "png"])

if uploaded:
    img = Image.open(uploaded)
    st.image(img, caption="Uploaded Image", use_column_width=True)

    # Convert image to base64 for API
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG")
    img_b64 = base64.b64encode(buffer.getvalue()).decode()

    st.subheader("🔍 AI Detection")
    st.write("Running livestock detection via Roboflow Cloud...")

    # Roboflow Hosted Infer API
    response = requests.post(
        "https://detect.roboflow.com/livestock/1",
        params={"api_key": ROBOFLOW_API},
        data=buffer.getvalue(),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    result = response.json()
    st.json(result)

    # Show detections
    if "predictions" in result:
        labels = [p["class"] for p in result["predictions"]]
        st.write("Detected Animals:", labels)
    else:
        st.warning("No livestock detected")

    # -----------------------
    # NFT Mint
    # -----------------------
    token_uri = st.text_input("Enter Token URI", "https://example.com/metadata.json")

    if st.button("Mint NFT"):
        try:
            nonce = w3.eth.get_transaction_count(account.address)
            tx = contract.functions.mintLivestockNFT(
                account.address,
                token_uri
            ).build_transaction({
                'from': account.address,
                'nonce': nonce,
                'gas': 300000,
                'gasPrice': w3.eth.gas_price,
            })

            signed = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
            tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)

            st.success("NFT Minted Successfully!")
            st.write("🔗 Tx:", f"https://sepolia.etherscan.io/tx/{tx_hash.hex()}")

        except Exception as e:
            st.error(str(e))
