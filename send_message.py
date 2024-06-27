import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.utils import formataddr
import os

EMAIL_SERVER = "smtp.gmail.com"
PORT = 465
SENDER_EMAIL = "khushi2003p@gmail.com"
PASSWORD_EMAIL = "oora cvcr sjjd upgb"

def send_message(name, receiver_email , token_count):
    msg = MIMEMultipart()
    msg["Subject"] = "InsightSync Web Services Billing Statement Available!"
    msg["From"] = formataddr(("InsightSync Team", SENDER_EMAIL))
    msg["To"] = receiver_email
    msg["BCC"] = SENDER_EMAIL

    body = f"""
    Hey there, {name}!

    Greetings from InsightSync,

A new billing invoice for the account ending in ****4416 is now available in your Billing and Cost Management Console. Your total amount is: INR{token_count}.

You can make a payment by using the “Pay Now” button on the “Orders and invoices” page: https://console.insightsync.com/billing/home#/paymenthistory on the Billing Management Console.

You can see a complete breakdown of all charges on the Billing and Cost Management Console located here: https://console.insightsync.com/billing/home#/bills?year=2024&month=4.

To receive future invoices in the PDF format, sign in to the InsightSync Management Console and open the InsightSync Billing console at https://console.insightsync.com/billing/ and opt-in to PDF invoices delivered by email under Invoice delivery preferences.

Thanks for being part of the InsightSync family.

Sincerely,

InsightSync

To learn more about managing your InsightSync costs with Cost Allocation and Tagging
, visit http://docs.insightsync.com/awsaccountbilling/latest/aboutv2/cost-alloc-tags.html.

This message was produced and distributed by InsightSync India Private Limited (InsightSync India), Block E, 14th Floor, Unit Nos. 1401 to 1421 International Trade Tower, Nehru Place, New Delhi, Delhi, 110019. InsightSync India will not be bound by, and specifically objects to, any term, condition or other provision which is different from or in addition to the provisions of the InsightSync Customer Agreement or InsightSync Enterprise Agreement between InsightSync India and you (whether or not it would materially alter such InsightSync Customer Agreement or InsightSync Enterprise Agreement) and which is submitted in any order, receipt, acceptance, confirmation, correspondence or otherwise, unless InsightSync India specifically agrees to such provision in a written instrument signed by InsightSync India. Your use of InsightSync products and services is governed by the InsightSync Customer Agreement linked below unless you purchase these 
products and services from an InsightSync Value Added Reseller.

    """
    msg.attach(MIMEText(body, "plain"))
    try:
        with smtplib.SMTP_SSL(EMAIL_SERVER, PORT) as server:
            server.login(SENDER_EMAIL, PASSWORD_EMAIL)
            server.sendmail(SENDER_EMAIL, receiver_email, msg.as_string())
            print(f"Email sent to {receiver_email}")
    except Exception as e:
        print(f"Error sending email: {e}")
