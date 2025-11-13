"""
Email notification tool for sending comments to PR managers.
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from datetime import datetime


class EmailSender:
    """Tool for sending email notifications to PR managers."""

    def __init__(
        self,
        smtp_server: str = "smtp.gmail.com",
        smtp_port: int = 587,
        email_from: Optional[str] = None,
        email_password: Optional[str] = None
    ):
        """
        Initialize email sender.

        Args:
            smtp_server: SMTP server address
            smtp_port: SMTP port
            email_from: Sender email address
            email_password: Sender email password or app password
        """
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.email_from = email_from
        self.email_password = email_password

    def send_comment_for_approval(
        self,
        pr_manager_email: str,
        executive_name: str,
        journalist_question: str,
        media_outlet: str,
        drafted_comment: str,
        humanized_comment: str,
        article_url: Optional[str] = None
    ) -> bool:
        """
        Send the humanized comment to PR manager for approval.

        Args:
            pr_manager_email: Email address of PR manager
            executive_name: Name of the executive
            journalist_question: The journalist's question
            media_outlet: Media outlet name
            drafted_comment: Original drafted comment
            humanized_comment: Humanized version of the comment
            article_url: Optional URL to the article

        Returns:
            True if email sent successfully, False otherwise
        """
        if not self.email_from or not self.email_password:
            print("Email credentials not configured. Skipping email send.")
            return False

        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"PR Comment Approval Needed - {executive_name} for {media_outlet}"
            msg["From"] = self.email_from
            msg["To"] = pr_manager_email

            # Create HTML content
            html_content = f"""
            <html>
              <head></head>
              <body>
                <h2>PR Comment Approval Request</h2>
                <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <hr>

                <h3>Details</h3>
                <p><strong>Executive:</strong> {executive_name}</p>
                <p><strong>Media Outlet:</strong> {media_outlet}</p>
                {f'<p><strong>Article URL:</strong> <a href="{article_url}">{article_url}</a></p>' if article_url else ''}

                <h3>Journalist Question</h3>
                <p style="background-color: #f5f5f5; padding: 15px; border-left: 4px solid #2196F3;">
                  {journalist_question}
                </p>

                <h3>Humanized Comment (Ready for Review)</h3>
                <div style="background-color: #e8f5e9; padding: 15px; border-left: 4px solid #4CAF50;">
                  {humanized_comment.replace(chr(10), '<br>')}
                </div>

                <h3>Original Drafted Comment (Reference)</h3>
                <details>
                  <summary>Click to expand</summary>
                  <div style="background-color: #fff3e0; padding: 15px; border-left: 4px solid #FF9800; margin-top: 10px;">
                    {drafted_comment.replace(chr(10), '<br>')}
                  </div>
                </details>

                <hr>
                <p><strong>Action Required:</strong> Please review the humanized comment and provide approval or request changes.</p>

                <p style="color: #666; font-size: 12px;">
                  This is an automated message from the PR Agent system.
                </p>
              </body>
            </html>
            """

            # Attach HTML content
            html_part = MIMEText(html_content, "html")
            msg.attach(html_part)

            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_from, self.email_password)
                server.send_message(msg)

            print(f"✓ Email sent successfully to {pr_manager_email}")
            return True

        except Exception as e:
            print(f"✗ Failed to send email: {str(e)}")
            return False

    def send_test_email(self, to_email: str) -> bool:
        """
        Send a test email to verify configuration.

        Args:
            to_email: Email address to send test to

        Returns:
            True if successful, False otherwise
        """
        if not self.email_from or not self.email_password:
            print("Email credentials not configured.")
            return False

        try:
            msg = MIMEMultipart()
            msg["Subject"] = "PR Agent - Test Email"
            msg["From"] = self.email_from
            msg["To"] = to_email

            body = "This is a test email from the PR Agent system. Configuration is working correctly!"
            msg.attach(MIMEText(body, "plain"))

            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_from, self.email_password)
                server.send_message(msg)

            print(f"✓ Test email sent to {to_email}")
            return True

        except Exception as e:
            print(f"✗ Test email failed: {str(e)}")
            return False
