from __future__ import annotations
import datetime
from typing import Optional
import discord
from discord.ext import commands
from discord import app_commands
from bot import Aswo
import re
from utils import default, osu_errors
from utils.osu import User
import socketio
class UserSelect(discord.ui.Select):
    def __init__(self, user: User):
        self.user = user
        options = [
    
            discord.SelectOption(label='Account Avatar', description=f'Shows the avatar of: {self.user.username}'),
            discord.SelectOption(label='Info', description=f'Info about: {self.user.username}'),
            discord.SelectOption(label="Statistics", description=f"Statistics about {self.user.username}")
        ]

        super().__init__(min_values=1, max_values=1, options=options, custom_id="OsuSelectID")

    async def callback(self, interaction: discord.Interaction):      
        await interaction.response.defer()
   
        if self.values[0] == "Account Avatar":
            embed = discord.Embed(color=0x2F3136)
            avatar_url = self.user.avatar_url

            embed.title = f"{self.user.username}'s Osu avatar"
            embed.set_image(url=avatar_url)

            await interaction.message.edit(embed=embed, view = DropdownView(interaction, interaction.user.id,self.user))

        if self.values[0] == "Statistics":
            embed = discord.Embed(title=f"{self.user.username}'s Statistics", color=0x2F3136)
            max_combo = self.user.max_combo
            play_style = ', '.join(self.user.playstyle) if type(self.user.playstyle) is list else f"{self.user.username} has no playstyles selected"
            embed.add_field(name="Total Statistics", value=f"Total Hits: {self.user.total_hits:,}\nTotal Score: {self.user.total_score:,}\nMaximum Combo: {max_combo}\nPlay Count: {self.user.play_count}", inline=True)
            embed.add_field(name="Play Styles", value=f"Play Styles: {play_style}\nFavorite Play Mode: {self.user.playmode}", inline=True)
            await interaction.message.edit(embed=embed, view = DropdownView(interaction, interaction.user.id,self.user))    


        if self.values[0] == "Info":
            embed = discord.Embed(color=0x2F3136)
            view = DropdownView(interaction, interaction.user.id,self.user)
            

            embed.description = f"**{self.user.country_emoji} | Profile for [{self.user.username}](https://osu.ppy.sh/users/{self.user.id})**\n\n▹ **Bancho Rank**: #{self.user.global_rank:,} ({self.user.country_code}#{self.user.country_rank:,})\n▹ **Join Date**: {self.user.joined_at}\n▹ **PP**: {int(self.user.pp):,} **Acc**: {self.user.accuracy}%\n▹ **Ranks**: {self.user.ranks}\n▹ **Profile Order**: \n** ​ ​ ​ ​ ​ ​ ​ ​  - {self.user.profile_order}**"
            embed.set_thumbnail(url=self.user.avatar_url)
            await interaction.message.edit(embed=embed, view=view)

class DropdownView(discord.ui.View):
    def __init__(self, itr: discord.Interaction, author_id: int ,user: User):
        super().__init__()
        self.itr = itr
        itr.client.http
        self.user = user
        self.author_id = author_id
        # Adds the dropdown to our view object.
        self.add_item(UserSelect(self.user))
    

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        
        await self.itr.edit_original_response(view=self)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:

        if interaction.user and interaction.user.id == self.author_id:
            return True
        await interaction.response.defer()
        await interaction.followup.send(f"You cant use this as you're not the command invoker, only the author (<@{interaction.guild.get_member(self.author_id).id}>) Can Do This!", ephemeral=True)
        return False




class osu(commands.Cog):
    def __init__(self, bot: Aswo):
        self.bot = bot
    
    osu = app_commands.Group(name="osu", description="All osu commands")
    set = app_commands.Group(name="set", description="allows you to set various things for osu", parent=osu)
    replay = app_commands.Group(name="replay", description="Allows you to control various aspects of replay uploading", parent=osu)

    
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        try:

            osr = message.attachments[0].url
            if osr.endswith('.osr'):
                skin = await self.bot.pool.fetchval("SELECT skin_id FROM replay_config WHERE user_id = $1", message.author.id)

                if skin is None:
                    skin = 1

                self.bot.logger.info(f"Skin : {skin}")

                async with self.bot.session.post("https://apis.issou.best/ordr/renders", data={"replayURL":osr, "username":"Aswo", "resolution":"1280x720", "skin": skin,"verificationKey":self.bot.replay_key}) as resp:
                    ordr_json = await resp.json()
                
                
                if ordr_json['errorCode'] == 8:
                    return await message.channel.send("This beatmap does not exist on osu!. Custom difficulties or non-submitted maps are not supported.\nSorry!")
                    
                mes = await message.channel.send("Osu replay file detected, a rendered replay will be sent shortly! May take up to a minute while its uploading so sit back and relax :D!\nIll ping you when its finished!")
                self.bot.logger.info(ordr_json)
                render_id = ordr_json['renderID']
                
                sio = socketio.AsyncClient()

                @sio.event
                async def render_done_json(data):
                    if data['renderID'] == render_id:
                        data = data
                        self.bot.logger.info(data)
                        await mes.edit(content=f"Here's your rendered video {message.author.mention}!\n{data['videoUrl']}")
                try:
                    await sio.connect('https://ordr-ws.issou.best')
                    await sio.wait()
                except socketio.exceptions.ConnectionError:
                    pass
        except IndexError:
            pass
            
    @osu.command()
    async def user(self, interaction: discord.Interaction, username: Optional[str]):
        """Gets info on osu account"""

        try:
            user_query = await self.bot.pool.fetchrow("SELECT osu_username FROM osu_user WHERE user_id = $1", interaction.user.id) 
            
            if user_query is None and username is None:
                user = await self.bot.osu.fetch_user(interaction.user.display_name)
            elif user_query is not None and username is None:
                user = await self.bot.osu.fetch_user(user_query.get("osu_username"))
            else:
                user = await self.bot.osu.fetch_user(username)

            
            self.bot.logger.info(user.username)
            self.bot.logger.info(user.avatar_url)
            view = DropdownView(interaction, interaction.user.id,user)
        
        
            embed = discord.Embed(description=f"**{user.country_emoji} | Profile for [{user.username}](https://osu.ppy.sh/users/{user.id})**\n\n▹ **Bancho Rank**: #{user.global_rank:,} ({user.country_code}#{user.country_rank:,})\n▹ **Join Date**: {user.joined_at}\n▹ **PP**: {int(user.pp):,} **Acc**: {user.accuracy}%\n▹ **Ranks**: {user.ranks}\n▹ **Profile Order**: \n** ​ ​ ​ ​ ​ ​ ​ ​  - {user.profile_order}**", color=0x2F3136)
            embed.set_thumbnail(url=user.avatar_url)
            await interaction.response.send_message(embed=embed, view=view)

        except osu_errors.NoUserFound:
            await interaction.response.send_message("No User Was Found Sadly!")

    @osu.command(description="Finds info on a beatmap")
    @app_commands.describe(beatmap="Beatmap to get info on")
    async def beatmap(self, itr: discord.Interaction, beatmap: str):
        beatmapid = re.findall(r"\d+", beatmap)[1]
        rbeatmap = await self.bot.osu.get_beatmap(beatmapid)
        ranked = discord.utils.format_dt(datetime.datetime.fromisoformat(rbeatmap.ranked_date.replace('Z', ''))) if rbeatmap.ranked_date else "Not Ranked!"
        updated = discord.utils.format_dt(datetime.datetime.fromisoformat(rbeatmap.last_updated.replace('Z', '')))
        submitted = discord.utils.format_dt(datetime.datetime.fromisoformat(rbeatmap.submitted_date.replace('Z', ''))) if rbeatmap.ranked_date else "Not Submitted!"
        creator = await self.bot.osu.fetch_user(rbeatmap.creator)


        embed = discord.Embed(title=f"Info on {rbeatmap.title}", color=0x2F3136)
        embed.add_field(name="Info", value=f"Creator of map: [{creator.username}](https://osu.ppy.sh/users/{creator.id})\nBeatmap ID: {rbeatmap.id}\nSong Artist: {rbeatmap.artist}\nStatus: {rbeatmap.status}\nFavorite count: {rbeatmap.favorite_count:,}\nPlayed count: {rbeatmap.play_count:,}\nMode: {rbeatmap.mode}")
        embed.add_field(name="Gameplay", value=f"Drain: {rbeatmap.drain}\nAR: {rbeatmap.ar}\nCS: {rbeatmap.cs}\nBPM: {rbeatmap.bpm}\nMax Combo: {rbeatmap.max_combo:,}")
        embed.add_field(name="Dates", value=f"Ranked date: {ranked}\nSubmitted date: {submitted}\nLast updated: {updated}", inline=False)
        embed.add_field(name="Links", value=f"[Link to beatmap]({rbeatmap.url}) • [kitsu.moe](https://kitsu.moe/d/{rbeatmap.beatmapset_id})")
        embed.set_image(url=rbeatmap.covers("card@2x"))



        await itr.response.send_message(embed=embed)

    @replay.command(description="Allows control on replay settings")
    @app_commands.describe(skin_id = "ID of a skin | https://ordr.issou.best/skins")
    async def config(self, itr: discord.Interaction, skin_id: int):
        try: 
            async with self.bot.session.get("https://apis.issou.best/ordr/skins", params={"pageSize": 400, "page":1}) as resp:
                skins = (await resp.json())['skins']
                self.bot.logger.info((await resp.json())['maxSkins'])

            query = """
                INSERT INTO replay_config (skin_id, user_id) VALUES($1, $2)
                ON CONFLICT(user_id) DO 
                UPDATE SET skin_id = excluded.skin_id
                RETURNING skin_id
            """
        
            await self.bot.pool.execute(query, skin_id, itr.user.id)
            skin_info = {skin['id']:{'preview': skin['highResPreview'], 'skin':skin['skin'], 'download': skin['url'], "author": skin['author']} for skin in skins}
            try:
                skin = skin_info[skin_id]
            except KeyError:
                return await itr.response.send_message("That skin is not accessable or for some reason the ordr api did not give us it, Sorry!", ephemeral=True)

            embed = discord.Embed(title=f"Succesfully made replay skin to {skin['skin']}!")
            embed.add_field(name='Download link', value=f"[Click here to download]({skin['download']})")
            embed.add_field(name="Author", value=skin['author'])
            embed.set_image(url=skin['preview'])


            return await itr.response.send_message(embed=embed)

        except Exception as e:
            return await itr.response.send_message(f"Oh No! an error occured!\n\nError Class: **{e.__class__.__name__}**\n{default.traceback_maker(err=e)}If you're a coder and you think this is a fatal error, DM Sawsha#0598!", ephemeral=True)

    @config.autocomplete('skin_id')
    async def id(self, itr: discord.Interaction, current: str):
        async with self.bot.session.get("https://apis.issou.best/ordr/skins", params={"pageSize": 400, "page":1}) as resp:
            skins = (await resp.json())['skins']
        if current == '':
            return [app_commands.Choice(name=skin['skin'], value=skin['id']) for skin in skins[1:25]]

        
        return [app_commands.Choice(name=skin['skin'], value=skin['id']) for skin in skins[1:25] if skin['id'] is int(current)]

        


    @set.command()
    async def user(self, interaction: discord.Interaction, username: str): 
        """Allows you to set your username""" 
        try:
            query = """
                INSERT INTO osu_user (osu_username, user_id) VALUES($1, $2)
                ON CONFLICT(user_id) DO 
                UPDATE SET osu_username = excluded.osu_username

            """
        
            await self.bot.pool.execute(query, username, interaction.user.id)

            await interaction.response.send_message(f"Sucessfullly set your osu username to: {username}")
        except Exception as e:
            return await interaction.response.send_message(f"Oh No! an error occured!\n\nError Class: **{e.__class__.__name__}**\n{default.traceback_maker(err=e)}If you're a coder and you think this is a fatal error, DM Sawsha#0598!", ephemeral=True)

    

async def setup(bot: Aswo):
    await bot.add_cog(osu(bot))	
