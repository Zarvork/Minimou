import os
import smtplib
import ssl
from datetime import datetime
from email.message import EmailMessage

import pygame
import pygame_gui


def send_canvas_by_email(canvas, recipient):
    os.makedirs("saved_paintings", exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"saved_paintings/painting_{timestamp}.png"

    # Save the current canvas
    pygame.image.save(canvas, filename)

    sender = "TODO_mail"
    password = "TODO_password"

    message = EmailMessage()
    message["Subject"] = "Your Pygame painting"
    message["From"] = sender
    message["To"] = recipient
    message.set_content("Here is the painting created in the Pygame installation.")

    with open(filename, "rb") as image_file:
        image_data = image_file.read()

    message.add_attachment(
        image_data, maintype="image", subtype="png", filename=os.path.basename(filename)
    )

    context = ssl.create_default_context()

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as smtp:
            smtp.login(sender, password)
            smtp.send_message(message)

        return True, "Painting sent successfully."

    except Exception as error:
        print("Email error:", error)
        return False, "Could not send the painting."
