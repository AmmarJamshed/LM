import streamlit as st
import requests
from web3 import Web3
from PIL import Image
import json
import io

st.set_page_config(page_title="LivestockMon", layout="wide")
st.title("🐄 LivestockMon — AI Livestock Detection + NFT Minting")

# --------------------------
# Secrets
# --------------------------
RPC_URL = st.secrets["blockchain"]["RPC_URL"]
PRIVATE_KEY = st.secrets["blockchain"]["PRIVATE_KEY"]
CONTRACT_ADDRESS = st.secrets["blockchain"]["CONTRACT_ADDRESS"]
ABI = json.loads(st.secrets["blockchain"]["ABI"])

ROBOFLOW_API = st.secrets["blockchain"]["ROBOFLOW_API"]
ROBOFLOW_MODEL = st.secrets["blockchain"]["ROBOFLOW_MODEL"]   # cows-mien3-33bgs
ROBOFLOW_VERSION = st.secrets["blockchain"]["ROBOFLOW_VERSION"]  # 1

# --------------------------
# Web3
# --------------------------
w3 = Web3(Web3.HTTPProvider(RPC_URL))
account = w3.eth.account.from_key(PRIVATE_KEY)
contract = w3.eth.contract(address=Web3.to_checksum_address(CONTRACT_ADDRESS), abi=ABI)

# --------------------------
# Upload Image
# --------------------------
file = st.file_uploader("Upload livestock image", type=["jpg", "jpeg", "png"])

if file:
    image = Image.open(file)
    st.image(image, caption="Uploaded Image", use_column_width=True)

    # Convert to bytes
    img_bytes = io.BytesIO()
    image.save(img_bytes, format="JPEG")
    img_bytes = img_bytes.getvalue()

    st.subheader("🔍 Running AI detection...")

    # --------------------------
    # Roboflow REST request
    # --------------------------
    url = f"https://detect.roboflow.com/{ROBOFLOW_MODEL}/{ROBOFLOW_VERSION}?api_key={ROBOFLOW_API}"

    response = requests.post(
        url,
        data=img_bytes,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )

    result = response.json()
    st.json(result)

    if "predictions" in result and len(result["predictions"]) > 0:
        labels = list({p["class"] for p in result["predictions"]})
        st.success(f"Detected: {labels}")
    else:
        st.warning("No livestock detected.")

    # --------------------------
    # NFT Mint
    # --------------------------
    st.subheader("🪙 Mint Livestock NFT")
    token_uri = st.text_input("Token URI:", "https://example.com/metadata.json")

    if st.button("Mint NFT"):
        try:
            nonce = w3.eth.get_transaction_count(account.address)
            tx = contract.functions.mintLivestockNFT(
                account.address,
                token_uri
            ).build_transaction({
                "from": account.address,
                "nonce": nonce,
                "gas": 300000,
                "gasPrice": w3.eth.gas_price
            })

            signed = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
            tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)

            st.success(f"NFT Minted!")
            st.write(f"https://sepolia.etherscan.io/tx/{tx_hash.hex()}")

        except Exception as e:
            st.error(str(e))
