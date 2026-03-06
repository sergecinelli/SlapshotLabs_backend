import datetime
import traceback
from users.models import CustomUser, UserInvitation
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string


def invite_users_to_website(emails: list[str], invited_by: CustomUser, invitation_details: dict, messages_addition: str = "") -> list[str]:
    """Invite users to the website.
    Returns a list of emails that failed to be invited."""
    failed_emails = []
    for email in emails:
        invitation = UserInvitation.objects.filter(email=email, invited_by=invited_by, invitation_details=invitation_details).first()
        if invitation:
            if invitation.send_email_error_timestamp is not None:
                # Previous sending failed, so we need to retry.
                invitation.send_email_error_message = None
                invitation.send_email_error_traceback = None
                invitation.send_email_error_timestamp = None
                should_send_email = True
            else:
                # Previous sending succeeded, so we don't need to send the email again,
                # just update the date and time the invitation was sent.
                invitation.invited_at = datetime.datetime.now(datetime.timezone.utc)
                should_send_email = False
            invitation.save()
        else:
            invitation = UserInvitation.objects.create(email=email, invited_by=invited_by, invitation_details=invitation_details)
            should_send_email = True
        if should_send_email:
            try:
                template_name = "registration/invitation_email.html"
                template_name_txt = "registration/invitation_email.txt"
                context = {
                    "email": email,
                    "invited_by": invited_by,
                    "invitation_token": invitation.invitation_token,
                    "invitation_object": invitation_details['object'],
                    "invitation_part": invitation_details['part'],
                    "messages_addition": (f" and {messages_addition}" if messages_addition else ""),
                    "frontend_url": settings.FRONTEND_URL
                }
                send_mail("User invitation", render_to_string(template_name_txt, context), settings.DEFAULT_FROM_EMAIL, [email],
                        html_message=render_to_string(template_name, context))
            except Exception as e:
                invitation.send_email_error_message = str(e)
                invitation.send_email_error_traceback = traceback.format_exc()
                invitation.send_email_error_timestamp = datetime.datetime.now(datetime.timezone.utc)
                invitation.save()
                failed_emails.append(email)
            else:
                invitation.invited_at = datetime.datetime.now(datetime.timezone.utc)
                invitation.save()
    return failed_emails