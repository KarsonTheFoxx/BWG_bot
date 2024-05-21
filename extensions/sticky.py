from disnake.ext import commands, plugins
from disnake import CommandInteraction, Embed, Color, Role, Member
import sqlite3
plugin = plugins.Plugin()

# Connects to the SQL database and creates tables if they are missing
connection = sqlite3.connect("data/database.db")
cursor = connection.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS Roles (roleid INTEGER PRIMARY KEY UNIQUE)")
cursor.execute("CREATE TABLE IF NOT EXISTS Users (userid INTEGER PRIMARY KEY UNIQUE, roleids TEXT)")
connection.commit()

# Command to add a sticky role
@plugin.slash_command(name="sticky", description="Adds the specified role to the sticky roles")
async def sticky(inter:CommandInteraction, role:Role):
    if inter.author.guild_permissions.manage_roles:
        await inter.response.defer()
        try:
            cursor.execute("INSERT INTO Roles (roleid) VALUES (?)", (role.id,))
        except sqlite3.IntegrityError:
            await inter.followup.send("Role already sticky!")
            return
        
        for user in role.members:
            try:
                cursor.execute("INSERT INTO Users (userid, roleids) VALUES (?, ?)", (user.id, str(role.id)+";"))
            except sqlite3.IntegrityError:
                try:
                    cursor.execute("SELECT * FROM Users WHERE userid = ?", str(user.id))
                    existing_user_data = cursor.fetchall()
                    if existing_user_data == []:
                        await inter.channel.send(f"Operation falied; cannot update user: {user.name}({user.id})")
                        return
                    existing_user_data = existing_user_data[0]
                    if not str(role.id) in existing_user_data[1]:
                        cursor.execute("UPDATE Users SET roleids = ? WHERE userid = ?", (";".join(existing_user_data[1]), user.id))
                except Exception:
                    await inter.channel.send("Failed to update users to have sticky roles. please manually re-apply the role to all users")
        connection.commit()
        await inter.followup.send(embed=Embed(title=f"Added glue to {role.name}!", description="Now the role is all sticky! Now you can't get rid of it!", color=Color.green()))
    else:
        await inter.response.send_message("You aren't allowed to do this", ephemeral=True)

# Command to remove a sticky role
@plugin.slash_command(name="unsticky")
async def unsticky(inter:CommandInteraction, role:Role):
    if inter.author.guild_permissions.manage_roles:
        await inter.response.defer()
        cursor.execute("DELETE FROM Roles WHERE roleid = ?", (role.id,))
        await inter.response.send_message("Removed sticky role")
        cursor.execute("SELECT * FROM Users WHERE ? IN (roleids)", (str(role.id)+";",))
        users = cursor.fetchall()
        for user in users:
            user_roles = user[1].replace(str(role.id)+';', "")
            cursor.execute("UPDATE Users SET roleids = ? WHERE userid = ?", (user_roles, user[0]))
        
        connection.commit()
        await inter.followup.send(embed=Embed(Title=f"Washed glue off the {role.name}!", description="Now you can lose the role.", color=Color.green()))
    else:
        await inter.response.send_message("You aren't allowed to do this", ephemeral=True)

@plugin.slash_command(name="verify-data", description="Verifies all data is stored correctly")
async def verify_integ(self, inter:CommandInteraction):
    if inter.author.id in plugin.bot.owner_ids:
        cursor.execute("SELECT * FROM Roles")
        roles = cursor.fetchall()
        
        cursor.execute("SELECT * FROM Users")
        users = cursor.fetchall()
        await inter.response.send_message(f"ROLES\n{roles}\n\nUSERS\n{users}")

@plugin.slash_command(name="reset-database")
async def reset(inter:CommandInteraction):
    cursor.execute("DELETE FROM Users")
    cursor.execute("DELETE FROM Roles")
    connection.commit()
    await inter.response.send_message("Reset database")

@plugin.listener("on_member_join")
async def on_join(member:Member):
    cursor.execute("SELECT * FROM Users WHERE userid = ?", (member.id,))
    member_data = cursor.fetchall()
    if member_data == []:
        await member.guild.get_channel(1237570069941194783).send(f"Welcome to {member.guild.name} {member.mention}")
    else:
        member_data = member_data[0]
        roles = [int(role.strip(" ")) for role in member_data[1].split(";") if role != ""]
        for role in roles:
            await member.add_roles(member.guild.get_role(role))

@plugin.listener("on_member_update")
async def member_update(before:Member, after:Member):
    if removed_role := set([role.id for role in before.roles]) - set([role.id for role in after.roles]):
        removed_role = list(removed_role)[0]
        cursor.execute("SELECT * FROM Roles")
        if len(sticky_roles := cursor.fetchall()) > 0:
            sticky_roles = [role[0] for role in sticky_roles]
            if removed_role in sticky_roles:
                cursor.execute("SELECT * FROM Users WHERE userid = ?", (after.id,))
                user = cursor.fetchall()
                if len(user) > 0:
                    cursor.execute("Update Users SET roleids = ? WHERE userid = ?", (user[0][1].replace(str(removed_role)+";", ""), after.id))

    
    elif added_role := set([role.id for role in after.roles]) - set([role.id for role in before.roles]):
        added_role = list(added_role)[0]
        cursor.execute("SELECT * FROM Roles")
        if len(sticky_roles := cursor.fetchall()) > 0:
            sticky_roles = [role[0] for role in sticky_roles]
            if added_role in sticky_roles:
                cursor.execute("SELECT * FROM Users WHERE userid = ?", (after.id,))
                user = cursor.fetchall()
                if len(user) > 0:
                    user = user[0]
                    user_roles = user[1] + str(added_role) + ";"
                    cursor.execute("UPDATE Users SET roleids = ? WHERE userid = ?", (user_roles, after.id))
                else:
                    cursor.execute("INSERT INTO Users (userid, roleid) VALUES (?, ?)", (after.id, str(added_role)+";"))

    connection.commit()

setup, teardown = plugin.create_extension_handlers()