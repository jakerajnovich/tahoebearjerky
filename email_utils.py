import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import secrets
from datetime import datetime, timedelta

load_dotenv()

# SMTP Configuration
SMTP_HOST = os.getenv('SMTP_HOST', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
SMTP_USER = os.getenv('SMTP_USER')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
SMTP_FROM_EMAIL = os.getenv('SMTP_FROM_EMAIL', 'noreply@sectorflow.ai')
SMTP_FROM_NAME = os.getenv('SMTP_FROM_NAME', 'TBJ')

# Store password reset tokens in memory (in production, use Redis or database)
password_reset_tokens = {}

def send_email(to_email, subject, html_content, text_content=None):
    """Send an email using SMTP"""
    try:
        msg = MIMEMultipart('alternative')
        msg['From'] = f"{SMTP_FROM_NAME} <{SMTP_FROM_EMAIL}>"
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # Add plain text version if provided
        if text_content:
            part1 = MIMEText(text_content, 'plain')
            msg.attach(part1)
        
        # Add HTML version
        part2 = MIMEText(html_content, 'html')
        msg.attach(part2)
        
        # Send email
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

def generate_password_reset_token(email):
    """Generate a password reset token"""
    token = secrets.token_urlsafe(32)
    expiry = datetime.now() + timedelta(hours=1)  # Token expires in 1 hour
    password_reset_tokens[token] = {
        'email': email,
        'expiry': expiry
    }
    return token

def verify_password_reset_token(token):
    """Verify a password reset token"""
    if token not in password_reset_tokens:
        return None
    
    token_data = password_reset_tokens[token]
    if datetime.now() > token_data['expiry']:
        del password_reset_tokens[token]
        return None
    
    return token_data['email']

def send_password_reset_email(to_email, reset_token):
    """Send password reset email"""
    reset_url = f"http://localhost:8000/reset-password.html?token={reset_token}"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: #4a7c59; color: white; padding: 20px; text-align: center; }}
            .content {{ background-color: #f9f9f9; padding: 30px; }}
            .button {{ display: inline-block; padding: 12px 30px; background-color: #4a7c59; color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
            .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Password Reset Request</h1>
            </div>
            <div class="content">
                <p>Hello,</p>
                <p>We received a request to reset your password for your Tahoe Bear Jerky account.</p>
                <p>Click the button below to reset your password:</p>
                <p style="text-align: center;">
                    <a href="{reset_url}" class="button">Reset Password</a>
                </p>
                <p>Or copy and paste this link into your browser:</p>
                <p style="word-break: break-all; color: #4a7c59;">{reset_url}</p>
                <p><strong>This link will expire in 1 hour.</strong></p>
                <p>If you didn't request this password reset, please ignore this email.</p>
            </div>
            <div class="footer">
                <p>&copy; 2025 Tahoe Bear Jerky. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    text_content = f"""
    Password Reset Request
    
    Hello,
    
    We received a request to reset your password for your Tahoe Bear Jerky account.
    
    Click this link to reset your password:
    {reset_url}
    
    This link will expire in 1 hour.
    
    If you didn't request this password reset, please ignore this email.
    
    © 2025 Tahoe Bear Jerky. All rights reserved.
    """
    
    return send_email(to_email, "Reset Your Password", html_content, text_content)

def send_order_confirmation_email(to_email, order_data):
    """Send order confirmation email"""
    order_number = order_data.get('order_number', 'N/A')
    total = order_data.get('total', 0)
    items = order_data.get('items', [])
    
    # Build items HTML
    items_html = ""
    for item in items:
        items_html += f"""
        <tr>
            <td style="padding: 10px; border-bottom: 1px solid #ddd;">{item['name']}</td>
            <td style="padding: 10px; border-bottom: 1px solid #ddd; text-align: center;">{item['quantity']}</td>
            <td style="padding: 10px; border-bottom: 1px solid #ddd; text-align: right;">${float(item['price']):.2f}</td>
        </tr>
        """
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: #4a7c59; color: white; padding: 20px; text-align: center; }}
            .content {{ background-color: #f9f9f9; padding: 30px; }}
            .order-details {{ background-color: white; padding: 20px; margin: 20px 0; border-radius: 5px; }}
            table {{ width: 100%; border-collapse: collapse; }}
            .total-row {{ font-weight: bold; font-size: 18px; }}
            .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>✓ Order Confirmed!</h1>
            </div>
            <div class="content">
                <p>Thank you for your order!</p>
                <p>Your order has been received and is being processed.</p>
                
                <div class="order-details">
                    <h2>Order #{order_number}</h2>
                    <table>
                        <thead>
                            <tr style="background-color: #f0f0f0;">
                                <th style="padding: 10px; text-align: left;">Item</th>
                                <th style="padding: 10px; text-align: center;">Qty</th>
                                <th style="padding: 10px; text-align: right;">Price</th>
                            </tr>
                        </thead>
                        <tbody>
                            {items_html}
                        </tbody>
                        <tfoot>
                            <tr class="total-row">
                                <td colspan="2" style="padding: 15px; text-align: right;">Total:</td>
                                <td style="padding: 15px; text-align: right;">${float(total):.2f}</td>
                            </tr>
                        </tfoot>
                    </table>
                </div>
                
                <p>We'll send you another email when your order ships.</p>
                <p>If you have any questions, please contact us at {SMTP_FROM_EMAIL}</p>
            </div>
            <div class="footer">
                <p>&copy; 2025 Tahoe Bear Jerky. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return send_email(to_email, f"Order Confirmation - #{order_number}", html_content)
