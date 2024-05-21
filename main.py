from disnake.ext import commands
from disnake import Intents, Activity, ActivityType, Status, Embed, Color
from asyncio import run
from os import system
async def main():
    intents = Intents.default()
    intents.message_content = True
    intents.members = True

    bot = commands.InteractionBot(owner_ids=[942954824352296970, 855948446540496896, 904284620001013781], intents=intents)
    TOKEN = open("token.txt", "r").read()

    @bot.event
    async def on_ready():
        print(f"Ready, logged in as: {bot.user.name}")
        await bot.change_presence(activity=Activity(name=":bread:", type=ActivityType.custom), status=Status.idle)

    @bot.slash_command(name="reload-extensions")
    async def reload_extensions(inter):
        if inter.author.id in bot.owner_ids:
            await inter.response.send_message(embed=Embed(title="Reloading extensions", color=Color.blurple()))
            try:
                extension_copy = list(bot.extensions.keys())
                for extension in extension_copy:
                    bot.reload_extension(extension)
                
                await inter.edit_original_message(embed=Embed(title="All Extensions reloaded", color=Color.green()))
                system("cls")
            except Exception as error:
                await inter.edit_original_message(embed=Embed(title="Failed to reload extensions", description=f"Extensions failed to load `last known extension: {extension}` caused by {error}", color=Color.red()))
                
    bot.load_extensions("extensions/")
    await bot.start(TOKEN)

run(main())