import logging
from typing import List, Optional
import requests
from app.config import settings

logger = logging.getLogger(__name__)

def send_book_available_email(
    to_email: str,
    book_title: str,
    book_author: str,
    item_id: str,
    copies_available: int,
    copies_total: int,
    copies_details: Optional[List[dict]] = None
) -> bool:
    subject = f"📚 הספר '{book_title}' זמין כעת ב{settings.LIBRARY_DISPLAY_NAME}!"
    
    copies_html = ""
    if copies_details:
        rows = "".join([
            f"<tr><td style='padding:6px;border:1px solid #ddd;'>{c.get('section', '')}</td>"
            f"<td style='padding:6px;border:1px solid #ddd;'>{c.get('barcode', '')}</td>"
            f"<td style='padding:6px;border:1px solid #ddd;color:green;font-weight:bold;'>{c.get('status', 'פנוי')}</td></tr>"
            for c in copies_details if c.get('is_available')
        ])
        copies_html = f"""
        <table style="width:100%; border-collapse:collapse; margin-top:15px; text-align:right;" dir="rtl">
            <tr style="background-color:#f0f4f8;">
                <th style="padding:6px;border:1px solid #ddd;">מדור</th>
                <th style="padding:6px;border:1px solid #ddd;">ברקוד</th>
                <th style="padding:6px;border:1px solid #ddd;">סטטוס</th>
            </tr>
            {rows}
        </table>
        """

    catalog_link = f"{settings.LIBRARY_BASE_URL}/BuildaGate8library/general2/product_card_edit.php?SiteName={settings.LIBRARY_SITE_NAME}&Clubtmp1=&CNumber=&NewNameMade={settings.LIBRARY_NEW_NAME_MADE}&ItemID={item_id}&Card=Card1&Daf=1"

    html_content = f"""
    <!DOCTYPE html>
    <html dir="rtl" lang="he">
    <head><meta charset="utf-8"></head>
    <body style="font-family: Arial, sans-serif; background-color: #f7fafc; padding: 20px; direction: rtl; text-align: right;">
        <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 8px; padding: 25px; border: 1px solid #e2e8f0; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
            <div style="text-align: center; border-bottom: 2px solid #124C99; padding-bottom: 15px; margin-bottom: 20px;">
                <h2 style="color: #124C99; margin: 0;">{settings.LIBRARY_DISPLAY_NAME}</h2>
                <p style="color: #718096; font-size: 14px; margin: 5px 0 0 0;">התראת זמינות ספרים</p>
            </div>
            
            <p style="font-size: 16px; color: #2d3748;">שלום,</p>
            <p style="font-size: 16px; color: #2d3748;">
                הספר שביקשת לעקוב אחריו הפך ל<strong>זמין להשאלה</strong> בספרייה!
            </p>
            
            <div style="background-color: #ebf8ff; border-right: 4px solid #3182ce; padding: 15px; border-radius: 4px; margin: 20px 0;">
                <h3 style="margin: 0 0 8px 0; color: #2b6cb0;">📖 {book_title}</h3>
                {f'<p style="margin: 0 0 5px 0; color: #4a5568;"><strong>מחבר/ת:</strong> {book_author}</p>' if book_author else ''}
                <p style="margin: 0; color: #4a5568;"><strong>עותקים פנויים:</strong> {copies_available} מתוך {copies_total}</p>
            </div>
            
            {copies_html}
            
            <div style="text-align: center; margin-top: 30px;">
                <a href="{catalog_link}" 
                   style="background-color: #124C99; color: #ffffff; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold; display: inline-block;">
                    צפייה בכרטיס הספר בקטלוג
                </a>
            </div>
            
            <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 30px 0 15px 0;">
            <p style="font-size: 12px; color: #a0aec0; text-align: center; margin: 0;">
                הודעה זו נשלחה באופן אוטומטי ממערכת ניטור הספרייה.
            </p>
        </div>
    </body>
    </html>
    """

    if not settings.BREVO_API_KEY:
        logger.warning(
            f"[EMAIL SIMULATION - No BREVO_API_KEY] To: {to_email} | Subject: {subject} | Available: {copies_available}/{copies_total}"
        )
        return True

    try:
        url = "https://api.brevo.com/v3/smtp/email"
        headers = {
            "accept": "application/json",
            "api-key": settings.BREVO_API_KEY,
            "content-type": "application/json",
        }
        payload = {
            "sender": {
                "name": settings.BREVO_SENDER_NAME,
                "email": settings.BREVO_SENDER_EMAIL
            },
            "to": [{"email": to_email}],
            "subject": subject,
            "htmlContent": html_content
        }
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        if response.status_code in (200, 201, 202):
            logger.info(f"Email successfully sent via Brevo to {to_email} for book '{book_title}'")
            return True
        else:
            logger.error(f"Brevo API error ({response.status_code}): {response.text}")
            return False
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
        return False
