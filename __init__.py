from nonebot.plugin.on import on_regex
from nonebot.rule import to_me
from nonebot.adapters.onebot.v11 import (
    Bot,
    MessageEvent,
    GroupMessageEvent,
    MessageSegment,
    Message
    )
from nonebot import logger
from pathlib import Path

import os
import re
import random
import nonebot
import requests
import unicodedata

try:
    import ujson as json
except ModuleNotFoundError:
    import json

Bot_NICKNAME: str = list(nonebot.get_driver().config.nickname)[0]

local = Path() / "data" / "MirlKoi"

# MirlKoi

MirlKoi_list = {}
MirlKoi_list["local"] = os.listdir(local)
MirlKoi_list["iw233"] = []
MirlKoi_list["top"] = []
MirlKoi_list["yin"] = []
MirlKoi_list["cat"] = []
MirlKoi_list["xing"] = []
MirlKoi_list["mp"] = []
MirlKoi_list["pc"] = []

MirlKoi_tag = {
    "色图 涩图 随机色图 随机涩图": "iw233",
    "推荐": "top",
    "白毛 白发 银发": "yin",
    "兽耳 猫耳 猫娘": "cat",
    "星空 夜空 星空壁纸 夜空壁纸": "xing",
    "竖屏壁纸 壁纸 手机壁纸": "mp",
    "电脑壁纸 横屏壁纸": "pc"
    }

MirlKoi = on_regex("^我?要.*[张份].+$|^来.*[张份].+$", rule = to_me(), priority = 50, block = True)

@MirlKoi.handle()
async def _(bot: Bot, event: MessageEvent):
    global MirlKoi_list, MirlKoi_tag
    msg = ""
    cmd = event.get_plaintext()

    N = re.sub(r'^我?要|^来|[张份].+$', '', cmd)
    N = N if N else 1

    try:
        N = int(N)
    except ValueError:
        try:
            N = int(unicodedata.numeric(N))
        except (TypeError, ValueError):
            N = 0

    if 1 <= N <= 10:
        msg += f"{Bot_NICKNAME}为你准备了{N}张随机壁纸。"
    elif N > 10:
        msg += f"{Bot_NICKNAME}为你的身体着想，为你准备了一张随机壁纸。"
        N = 1
    else:
        msg += f"没有听懂呢，不过{Bot_NICKNAME}送你一张随机壁纸。"
        N = 1

    tag = re.sub(r'^我?要|^来|.*[张份]', '', cmd)

    for x in MirlKoi_tag.keys():
        if tag in x.split():
            msg += f"\n来源：{tag}"
            tag = MirlKoi_tag[x]
            break
        else:
            continue
    else:
        msg += f"\n来源不存在。\n已自动切换到来源：推荐。\n可选：推荐 白毛 兽耳 星空壁纸 手机壁纸 电脑壁纸"
        tag = "top"

    if len(MirlKoi_list[tag]) < N:
        logger.info(f"正在从MirlKoi获取图片，来源：{tag}")
        resp = requests.get(f"https://iw233.cn/api.php?sort={tag}&type=json&num=100")
        if resp.status_code == 200:
            resp = resp.text
            resp = ''.join(x for x in resp if x.isprintable())
            MirlKoi_list[tag] += json.loads(resp)["pic"]
        else:
            msg += f"\n呜......连接出错了...\n但是{Bot_NICKNAME}为你准备了一张本地图片~"
            tag = "local"
    else:
        logger.info(f"正在从本地队列获取图片，来源：{tag}")

    if tag == "local":
        image = MessageSegment.image(file = local / random.choice(MirlKoi_list["local"]))
        await MirlKoi.send(Message(msg) + image , at_sender = True)
    elif N <= 3:
        image = Message()
        for i in range(N):
            image +=  MessageSegment.image(file = MirlKoi_list[tag][0])
            MirlKoi_list[tag].pop(0)
        await MirlKoi.send(Message(msg) + image, at_sender = True)
    else:
        await MirlKoi.send(msg, at_sender = True)
        msg_list =[]
        for i in range(N):
            msg_list.append(
                {
                    "type": "node",
                    "data": {
                        "name": Bot_NICKNAME,
                        "uin": event.self_id,
                        "content": MessageSegment.image(file = MirlKoi_list[tag][0])
                        }
                    }
                )
            MirlKoi_list[tag].pop(0)
        if isinstance(event,GroupMessageEvent):
            await bot.send_group_forward_msg(group_id = event.group_id, messages = msg_list)
        else:
            await bot.send_private_forward_msg(user_id = event.user_id, messages = msg_list)