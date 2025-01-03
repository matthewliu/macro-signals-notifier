import sendgrid
import sendgrid.helpers.mail as sgh
from config import constants

class Email(object):
    def __init__(self, email, name=None):
        self.email = email
        self.name = name or email  # Use email as name if none provided

class Attachment(object):
    def __init__(self, content, type, file_name, disposition, content_id):
        self.content = content
        self.type = type
        self.file_name = file_name
        self.disposition = disposition
        self.content_id = content_id

def send_message(sender, recipients, subject, body_text, body_html, 
                attachments=None, ccs=None, bccs=None, categories=None, send=True):
    """
    Send an email using SendGrid
    Args:
        sender (Email): Sender email object
        recipients (list[Email]): List of recipient Email objects
        subject (str): Email subject
        body_text (str): Plain text email content
        body_html (str): HTML email content
        attachments (list[Attachment], optional): List of attachments
        ccs (list[Email], optional): List of CC recipients
        bccs (list[Email], optional): List of BCC recipients
        categories (list[str], optional): List of email categories
        send (bool, optional): Whether to send immediately or return mail object
    Returns:
        Response from SendGrid API if send=True, otherwise returns Mail object
    """
    try:
        sg_api = sendgrid.SendGridAPIClient(constants.SENDGRID_API_KEY)
        mail = sgh.Mail()
        mail.from_email = sgh.Email(sender.email, sender.name)
        
        # Add DEV prefix if in development environment
        if 'localhost' in constants.HOST or 'pagekite' in constants.HOST:
            subject = f'[DEV] {subject}'
            body_html = f'<div style="color: #EA3943; margin-bottom: 15px;">[DEVELOPMENT ENVIRONMENT]</div>{body_html}'
            body_text = f'[DEVELOPMENT ENVIRONMENT]\n\n{body_text}'
        
        mail.subject = subject
        
        for recipient in recipients:
            personalization = sgh.Personalization()
            personalization.add_to(sgh.Email(recipient.email, recipient.name))
            if ccs:
                for cc in ccs:
                    personalization.add_cc(sgh.Email(cc.email))
            if bccs:
                for bcc in bccs:
                    personalization.add_bcc(sgh.Email(bcc.email))
            mail.add_personalization(personalization)

        mail.add_content(sgh.Content("text/plain", body_text))
        mail.add_content(sgh.Content("text/html", body_html))

        if attachments:
            for attach in attachments:
                attachment = sgh.Attachment()
                attachment.file_content = sgh.FileContent(attach.content)
                attachment.file_type = sgh.FileType(attach.type)
                attachment.file_name = sgh.FileName(attach.file_name)
                attachment.disposition = sgh.Disposition(attach.disposition)
                attachment.content_id = sgh.ContentId(attach.content_id)
                mail.add_attachment(attachment)

        if categories:
            for category in categories:
                mail.add_category(sgh.Category(category))

        if send:
            response = sg_api.client.mail.send.post(request_body=mail.get())
            if response.status_code not in [200, 201, 202]:
                print(f"Failed to send email. Status code: {response.status_code}")
                return False
            return True
        return mail
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False



