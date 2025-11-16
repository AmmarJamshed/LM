import streamlit as st
import requests
from web3 import Web3
from PIL import Image
import json
import io

st.set_page_config(page_title="LivestockMon", layout="wide")
st.title("🐄 LivestockMon — AI Livestock Detection + NFT Minting")


# ----------------------------------------
# Load secrets from Streamlit Cloud
# ----------------------------------------
RPC_URL = st.secrets["blockchain"]["RPC_URL"]
PRIVATE_KEY = st.secrets["blockchain"]["PRIVATE_KEY"]
CONTRACT_ADDRESS = st.secrets["blockchain"]["CONTRACT_ADDRESS"]
ABI = json.loads(st.secrets["blockchain"]["ABI"])

ROBOFLOW_API = st.secrets["blockchain"]["ROBOFLOW_API"]
ROBOFLOW_MODEL = st.secrets["blockchain"]["ROBOFLOW_MODEL"]     # e.g. cows-mien3-33bgs
ROBOFLOW_VERSION = st.secrets["blockchain"]["ROBOFLOW_VERSION"] # e.g. 1


# ----------------------------------------
# Web3 initialization
# ----------------------------------------
w3 = Web3(Web3.HTTPProvider(RPC_URL))
account = w3.eth.account.from_key(PRIVATE_KEY)
contract = w3.eth.contract(
    address=Web3.to_checksum_address(CONTRACT_ADDRESS),
    abi=ABI
)


# ----------------------------------------
# UI Upload
# ----------------------------------------
file = st.file_uploader("Upload livestock image", type=["jpg", "jpeg", "png"])

if file:
    image = Image.open(file)
    st.image(image, caption="Uploaded Image", use_column_width=True)

    # Convert image safely to RGB
    buf = io.BytesIO()
    if image.mode != "RGB":
        image = image.convert("RGB")
    image.save(buf, format="JPEG")
    img_bytes = buf.getvalue()

    st.subheader("🔍 Running AI detection...")

    # ----------------------------------------
    # Roboflow REST API call
    # ----------------------------------------
    url = f"https://detect.roboflow.com/{ROBOFLOW_MODEL}/{ROBOFLOW_VERSION}?api_key={ROBOFLOW_API}"

    response = requests.post(
        url,
        files={"file": img_bytes}  # <-- FIXED, correct API usage
    )

    try:
        result = response.json()
    except:
        st.error("Roboflow returned invalid response.")
        st.stop()

    st.json(result)

    # Extract detected classes
    if "predictions" in result and len(result["predictions"]) > 0:
        labels = list({p["class"] for p in result["predictions"]})
        st.success(f"Detected: {', '.join(labels)}")
    else:
        st.warning("No livestock detected.")


    # ----------------------------------------
    # NFT Minting Section
    # ----------------------------------------
    st.subheader("🪙 Mint Livestock NFT")

    token_uri = st.text_input(
        "Enter Token URI:",
        "https://example.com/metadata.json"
    )

    # Mint NFT Button
if st.button("Mint NFT"):
    # Validate Secrets
    if not RPC_URL or not PRIVATE_KEY:
        st.error("Missing blockchain credentials in Streamlit Secrets!")
    else:
        try:
            # Load contract
            contract = w3.eth.contract(
                address=Web3.to_checksum_address(CONTRACT_ADDRESS),
                abi=ABI
            )

            # Wallet
            account = w3.eth.account.from_key(PRIVATE_KEY)

            # Build transaction
            tx = contract.functions.mintLivestockNFT(
                account.address,
                token_uri
            ).build_transaction({
                "from": account.address,
                "nonce": w3.eth.get_transaction_count(account.address),
                "gas": 300000,
                "gasPrice": w3.eth.gas_price
            })

            # Sign
            signed_tx = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)

            # Send + prepend 0x FIX
            raw_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            tx_hash = "0x" + raw_hash.hex()

            # Explorer link
            etherscan_url = f"https://sepolia.etherscan.io/tx/{tx_hash}"

            st.success("NFT Minted Successfully!")
            st.markdown(f"[View Transaction on Etherscan]({etherscan_url})")

        except Exception as e:
            st.error(f"Error: {str(e)}")
