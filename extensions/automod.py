from disnake.ext import plugins, commands
from disnake import Message, Embed, Color, File
import sqlite3

messages = {}
plugin = plugins.Plugin()
@plugin.listener("on_message")
async def automod(message:Message):
    global messages
    if not message.author.bot:
        # Adds user to the cache if they have not already
        if str(message.author.id) in messages.keys():
            messages[str(message.author.id)].append(message.content.lower())
        else:
            messages[str(message.author.id)] = [message.content.lower()]
        messages[str(message.author.id)] = messages[str(message.author.id)][-3:]
        if len(set(messages[str(message.author.id)])) < 2 and len(messages[str(message.author.id)]) > 1 and not "Administrator" in message.author.guild_permissions:
            await message.author.send(embed=Embed(title="Anti Spam filter triggered", description="The anti spam trigger was failed. Please avoid sending the same message repeatedly.", color=Color.red()))
            await message.author.timeout(duration=600)
            for spam in await message.channel.history(limit=4).flatten():
                if spam.author == message.author:
                    await spam.delete()
        
setup, teardown = plugin.create_extension_handlers()