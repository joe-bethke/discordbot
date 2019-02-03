import discord
from dotenv import load_dotenv
import os
from random import choice

from complements import complement_list
from data_tracking import MemberDocument

load_dotenv("auth.env")
TOKEN = os.getenv("TOKEN")

client = discord.Client()


def default_channel(server):
    return next(channel for channel in server.channels
                if channel.name == "general" or channel == server.default_channel)


def complement(member, server):
    message = choice(complement_list)
    return message.format(server=server.name, name=member.name)


@client.event
async def on_member_join(member):
    MemberDocument(member)  # Create a new member
    await client.send_message(default_channel(member.server), complement(member, member.server))


@client.event
async def on_voice_state_update(before, after):
    before_doc = MemberDocument(before)
    if before.voice.voice_channel is None and after.voice.voice_channel is not None:
        before_doc.connection()
        await client.send_message(default_channel(before.server), complement(before, before.server))
    if before.voice_channel is not None and after.voice_channel is None:
        before_doc.disconnection()
        if before.voice.is_afk or (before.voice.self_mute or before.voice.self_deaf):
            await client.send_message(default_channel(before.server),
                                      "Okay bye {n}... thanks for the warm goodbye...".format(n=before.name))
    if not before.voice.is_afk and after.voice.is_afk:
        before_doc.afk()
    if before.voice.is_afk and not after.voice.is_afk:
        before_doc.afk_exit()


@client.event
async def on_message(message):
    member_doc = MemberDocument(message.author)
    member_doc.message(str(message.content))


client.run(TOKEN)
