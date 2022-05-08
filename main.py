import nightcore as nc
import os
import requests
import json
from config import *
from vkbottle.bot import Bot, Message
from vkbottle.api import API
from vkbottle.tools import AudioUploader

bot = Bot(BOT_TOKEN)
user = API(USER_TOKEN)

sharers: int = []

async def repost_checker() -> None:
    reposts = await user.request("wall.getReposts", {"owner_id": GROUP_ID*-1, "post_id": REPOST_POST_ID, "count": 1000})

    for repost in reposts["response"]["items"]:
        if repost["from_id"] < 0:
            continue
        sharers.append(repost["from_id"])

def is_sharer(user_id: int) -> bool:
    for sharer in sharers:
        if sharer == user_id:
            return True
    return False

bot.loop_wrapper.add_task(repost_checker())

@bot.on.message()
async def handler(message: Message) -> str:
    if not message.attachments:
        return "отправь мне аудио!"

    from_id = message.from_id
    for attachment in message.attachments:
        if attachment.type.value == "audio":
            if attachment.audio.duration > DURATION_LIMIT: continue
            await message.reply("обрабатываем..")

            doc = requests.get(attachment.audio.url)
            with open(f"pre{from_id}.mp3", 'wb') as f:
                f.write(doc.content)

            nc_audio = f"pre{from_id}.mp3" @ nc.Tones(TONES)
            nc_audio.export(f"out{from_id}.mp3")
            os.remove(f"pre{from_id}.mp3")

            water_mark = "" if is_sharer(from_id) else WATERMARK
            response = await AudioUploader(user, generate_attachment_strings=False).upload(attachment.audio.artist.lower(), f"{attachment.audio.title}{water_mark}".lower(), f"out{from_id}.mp3")
            r = await user.request("audio.add", {"audio_id": response["id"], "owner_id": response["owner_id"], "group_id": GROUP_ID})
            await message.answer(f"ваш найткор!", attachment=f"audio{GROUP_ID*-1}_{r['response']}")
            await message.answer(sticker_id=14)
            os.remove(f"out{from_id}.mp3")

@bot.on.raw_event("wall_repost")
async def handler_reposts(data: dict):
    if data["object"]["copy_history"][0] == REPOST_POST_ID:
        user_id = data["object"]["from_id"]
        if user_id < 0:
            return
        if not is_sharer(user_id):
            sharers.append(sharer)

bot.run_forever()
