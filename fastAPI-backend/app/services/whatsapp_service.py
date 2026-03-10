# ✅ Fix — run sync Twilio call in a thread pool
import asyncio
from functools import partial
from fastapi import HTTPException
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from app.core.config import settings

client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

async def send_whatsapp_otp(phone: str, otp: str):
    loop = asyncio.get_event_loop()
    try:
        message = await loop.run_in_executor(
            None,
            partial(
                client.messages.create,
                body=f"Your OTP is {otp}. Valid for 5 minutes.",
                from_=settings.TWILIO_WHATSAPP_NUMBER,
                to=f"whatsapp:{phone}"
            )
        )
        return message.sid
    except TwilioRestException as e:
        raise HTTPException(status_code=502, detail=f"Twilio error: {e.msg}")