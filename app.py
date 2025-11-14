import streamlit as st
from ultralytics import YOLOv8
from web3 import Web3
import json
from PIL import Image

st.set_page_config(page_title="LivestockMon", layout="wide")
st.title("🐮 LivestockMon – AI Livestock Detection + NFT Minting")

# -------------------------
# Load Secrets
# -------------------------
RPC_URL = st.secrets["blockchain"]["RPC_URL"]
PRIVATE_KEY = st.secrets["blockchain"]["PRIVATE_KEY"]
CONTRACT_ADDRESS = st.secrets["blockchain"]["CONTRACT_ADDRESS"]
ABI = json.loads(st.secrets["blockchain"]["ABI"])

# -------------------------
# Blockchain Setup
# -------------------------
w3 = Web3(Web3.HTTPProvider(RPC_URL))
account = w3.eth.account.from_key(PRIVATE_KEY)
contract = w3.eth.contract(address=Web3.to_checksum_address(CONTRACT_ADDRESS), abi=ABI)

# -------------------------
# Load YOLOv8 from HuggingFace
# -------------------------
@st.cache_resource
def load_model():
    return YOLOv8.from_pretrained("Ultralytics/YOLOv8")

model = load_model()

st.subheader("📸 Upload Livestock Image")
uploaded_file = st.file_uploader("Upload an image...", type=["jpg", "jpeg", "png"])

if uploaded_file:
    img = Image.open(uploaded_file)
    st.image(img, caption="Uploaded Image", use_column_width=True)

    st.write("Running AI detection...")
    results = model.predict(source=img)

    # Display prediction results
    st.subheader("🔍 Detection Results")
    st.json(results[0].to_json())

    # Extract simplified detection labels
    st.write("Detected objects:")
    labels = [model.names[int(box.cls)] for box in results[0].boxes]
    st.write(labels)

    # Token URI (metadata URL)
    token_uri = st.text_input("Enter tokenURI for NFT", "https://example.com/metadata.json")

    if st.button("Mint Livestock NFT"):
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

            signed_tx = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
            tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)

            st.success(f"NFT Minted Successfully!")
            st.write(f"🔗 Transaction: https://sepolia.etherscan.io/tx/{tx_hash.hex()}")

        except Exception as e:
            st.error(f"Minting failed: {str(e)}")

