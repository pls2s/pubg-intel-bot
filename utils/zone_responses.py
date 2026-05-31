from __future__ import annotations

import asyncio
import logging

from aiogram.types import Message

from models.zone import ZonePrediction
from utils.formatters import format_zone_prediction
from utils.telegram import answer_photo_bytes, answer_text
from utils.zone_image import render_zone_prediction_image


logger = logging.getLogger(__name__)


async def answer_zone_prediction(message: Message, prediction: ZonePrediction) -> None:
    """Send a generated zone-prediction image followed by the detailed text."""

    text = format_zone_prediction(prediction)
    image_sent = False

    if prediction.map_data or prediction.phase:
        try:
            image_bytes = await asyncio.to_thread(render_zone_prediction_image, prediction)
        except Exception as exc:  # Generated visuals should never block text answers.
            logger.warning("Could not render zone prediction image: %s", exc)
        else:
            caption = _caption(prediction)
            image_sent = await answer_photo_bytes(
                message,
                image_bytes,
                filename="pubg-zone-prediction.png",
                caption=caption,
            )

    await answer_text(message, text if not image_sent else f"รายละเอียด:\n{text}")


def _caption(prediction: ZonePrediction) -> str:
    parts = ["รูปทำนายวง"]
    if prediction.map_data:
        parts.append(prediction.map_data.display_name)
    if prediction.phase:
        parts.append(f"Phase {prediction.phase.phase}")
    return " | ".join(parts)
