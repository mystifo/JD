"""Email helpers. Templates never interpolate user content (BR-10)."""

import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template import TemplateDoesNotExist
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


def send_template(template_name, *, subject, to, context=None, reply_to=None):
    """Render `templates/email/<template_name>.txt` and send it.

    Callers must only pass display names, dates, and links in `context`.
    """
    context = context or {}
    body = render_to_string(f"email/{template_name}.txt", context)
    message = EmailMultiAlternatives(
        subject=subject,
        body=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[to],
        reply_to=reply_to or None,
    )
    try:
        html = render_to_string(f"email/{template_name}.html", context)
    except TemplateDoesNotExist:
        html = ""
    if html.strip():
        message.attach_alternative(html, "text/html")
    message.send()
    logger.info("email_sent", extra={"template": template_name})
    return True
