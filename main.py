from fastapi import FastAPI, HTTPException, Header, UploadFile, File, Form
import smtplib
from email.message import EmailMessage
import logging
import re

API_KEY = "my-secret-key"
SMTP_HOST = "localhost"
SMTP_PORT = 1025

logging.basicConfig(
    filename="mail.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

app = FastAPI()

def validate_email(email: str):
    pattern = r"^[a-zA-Z0-9._-]+@aumovio\.com$"
    if not re.match(pattern, email):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid company email: {email}"
        )

@app.post("/send-mail")
async def send_mail(
    to: str = Form(...),
    subject: str = Form(...),
    body: str = Form(...),
    isHtml: bool = Form(False),
    file: UploadFile = File(None),
    x_api_key: str = Header(...)
):
    
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")

    try:
    
        recipients = [email.strip() for email in to.split(",")]

        for email in recipients:
            validate_email(email)

       
        if not subject.strip() or not body.strip():
            raise HTTPException(
                status_code=400,
                detail="Subject and body cannot be empty"
            )

        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = "noreply@aumovio.com"
        msg["To"] = ", ".join(recipients)

        if isHtml:
            msg.add_alternative(body, subtype="html")
        else:
            msg.set_content(body)

    
        if file:
            content = await file.read()
            msg.add_attachment(
                content,
                maintype="application",
                subtype="octet-stream",
                filename=file.filename
            )

      
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.send_message(msg)

        logging.info(f"Email sent to {recipients}" + (f" with attachment {file.filename}" if file else ""))

        return {
            "status": "success",
            "message": "Email sent successfully"
        }

    except HTTPException:
        raise

    except Exception as e:
        logging.error(f"Error sending email: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send email: {str(e)}"
        )

# HEALTH CHECK
@app.get("/")
def root():
    return {"message": "Mail API is running"}