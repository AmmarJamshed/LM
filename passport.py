import streamlit as st
from web3 import Web3
import json
import requests
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
import qrcode
import io

st.set_page_config(page_title="Livestock Passport Builder")

# -------------------------------------
# Blockchain Setup
# -------------------------------------
RPC_URL = st.secrets["blockchain"]["RPC_URL"]
CONTRACT_ADDRESS = st.secrets["blockchain"]["CONTRACT_ADDRESS"]
ABI = json.loads(st.secrets["contract"]["ABI"])

web3 = Web3(Web3.HTTPProvider(RPC_URL))
contract = web3.eth.contract(address=Web3.to_checksum_address(CONTRACT_ADDRESS), abi=ABI)

st.title("🐄 LivestockMon - Passport Generator")

# -------------------------------------
# User Input
# -------------------------------------
token_id = st.number_input("Enter Token ID", min_value=0)

if st.button("Generate Passport PDF"):

    with st.spinner("Fetching NFT data..."):

        try:
            token_uri = contract.functions.tokenURI(token_id).call()
            metadata = requests.get(token_uri).json()
            image_url = metadata.get("image", "")
        except:
            st.error("❌ NFT not found or unable to fetch metadata.")
            st.stop()

        # Download image
        img_bytes = requests.get(image_url).content
        img_stream = io.BytesIO(img_bytes)

        # Make QR code of metadata URL
        qr = qrcode.make(token_uri)
        qr_bytes = io.BytesIO()
        qr.save(qr_bytes, format="PNG")
        qr_bytes.seek(0)

    # -------------------------------------
    # Generate PDF
    # -------------------------------------
    pdf_buffer = io.BytesIO()
    pdf = canvas.Canvas(pdf_buffer, pagesize=A4)
    width, height = A4

    # Header
    pdf.setFont("Helvetica-Bold", 22)
    pdf.drawString(50, height - 50, "🪪 LivestockMon - Animal Passport")

    # Image
    pdf.drawImage(ImageReader(img_stream), 50, height - 400, width=300, preserveAspectRatio=True, mask='auto')

    # QR Code
    pdf.drawImage(ImageReader(qr_bytes), 380, height - 350, width=150, preserveAspectRatio=True, mask='auto')

    # Details
    pdf.setFont("Helvetica", 14)
    pdf.drawString(50, height - 430, f"Token ID: {token_id}")
    pdf.drawString(50, height - 450, f"Owner: {web3.eth.default_account or 'Your Wallet'}")
    pdf.drawString(50, height - 470, f"Metadata URI:")
    pdf.setFont("Helvetica", 12)
    pdf.drawString(50, height - 490, token_uri)

    # Metadata fields
    y = height - 520
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(50, y, "Metadata:")
    pdf.setFont("Helvetica", 12)

    for k, v in metadata.items():
        y -= 20
        pdf.drawString(60, y, f"{k}: {v}")

    pdf.showPage()
    pdf.save()
    pdf_buffer.seek(0)

    st.success("Passport generated successfully!")

    # Download button
    st.download_button(
        label="📄 Download Livestock Passport PDF",
        data=pdf_buffer,
        file_name=f"Livestock_Passport_{token_id}.pdf",
        mime="application/pdf"
    )
