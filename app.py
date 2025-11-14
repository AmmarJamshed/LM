import streamlit as st
from inference_sdk import InferenceHTTPClient
from web3 import Web3
import json
from PIL import Image
import io

st.set_page_config(page_title="LivestockMon", layout="wide")
st.title("🐄 LivestockMon — AI Livestock Detection + NFT Minting")

# ---------------------------
# Load Secrets from Streamlit Cloud
# ---------------------------
RPC_URL = st.secrets["blockchain"]["RPC_URL"]
PRIVATE_KEY = st.secrets["blockchain"]["PRIVATE_KEY"]
CONTRACT_ADDRESS = st.secrets["blockchain"]["CONTRACT_ADDRESS"]
ABI = json.loads(st.secrets["blockchain"]["ABI"])

# Roboflow API
ROBOFLOW_API = st.secrets["blockchain"]["ROBOFLOW_API"]
ROBOFLOW_MODEL_ID = st.secrets["blockchain"]["ROBOFLOW_MODEL_ID"]  # ex. cows-mien3-33bgs/1

# ---------------------------
# Blockchain Setup
# ---------------------------
w3 = Web3(Web3.HTTPProvider(RPC_URL))
account = w3.eth.account.from_key(PRIVATE_KEY)
contract = w3.eth.contract(
    address=Web3.to_checksum_address(CONTRACT_ADDRESS), abi=ABI
)

# ---------------------------
# Roboflow Inference client
# ---------------------------
CLIENT = InferenceHTTPClient(
    api_url="https://serverless.roboflow.com",
    api_key=ROBOFLOW_API
)

# ---------------------------
# Upload Image
# ---------------------------
uploaded = st.file_uploader("Upload a livestock image", type=["jpg", "jpeg", "png"])

if uploaded:
    img = Image.open(uploaded)
    st.image(img, caption="Uploaded Image", use_column_width=True)

    # Convert image for inference
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    img_bytes = buf.getvalue()

    st.subheader("🔍 Running AI Livestock Detection...")

    # ---------------------------
    # Run inference
    # ---------------------------
    result = CLIENT.infer(img_bytes, model_id=ROBOFLOW_MODEL_ID)
    st.json(result)

    # Display labels
    if "predictions" in result:
        labels = list({p["class"] for p in result["predictions"]})
        st.success(f"Detected animals: {', '.join(labels)}")
    else:
        st.warning("No livestock detected.")

    # ---------------------------
    # NFT MINT SECTION
    # ---------------------------
    st.subheader("🪙 Mint Livestock NFT")
    token_uri = st.text_input("Enter Token URI:", "https://example.com/metadata.json")

    if st.button("Mint NFT"):
        try:
            nonce = w3.eth.get_transaction_count(account.address)
            tx = contract.functions.mintLivestockNFT(
                account.address,
                token_uri
            ).build_transaction({
                "from": account.address,
                "nonce": nonce,
                "gas": 350000,
                "gasPrice": w3.eth.gas_price
            })

            signed_tx = w3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY)
            tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)

            st.success("NFT Minted Successfully!")
            st.write("Transaction:", f"https://sepolia.etherscan.io/tx/{tx_hash.hex()}")

        except Exception as e:
            st.error(str(e))
