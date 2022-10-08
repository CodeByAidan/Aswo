from __future__ import annotations
import datetime
from typing import Any, Dict, List, Union
import typing
import aiohttp
from .default import date
from .osu_errors import NoUserFound, NoBeatMapFound

class Osu:
    def __init__(self, *, client_id: int, client_secret: str, session: aiohttp.ClientSession):
        self.id = client_id
        self.secret = client_secret
        self.session: aiohttp.ClientSession = session
        self.API_URL = "https://osu.ppy.sh/api/v2"
        self.TOKEN_URL = "https://osu.ppy.sh/oauth/token"
        self.beatmap_types = ['favourite', 'graveyard', 'loved', 'most_played', 'pending', 'ranked']
    
    async def get_token(self):
        data = {
            "client_id": self.id,
            "client_secret":self.secret,
            'grant_type':'client_credentials',
            'scope':"public",
        }


        async with self.session.post(self.TOKEN_URL,data=data) as response:
            return (await response.json()).get("access_token")
    
    async def make_headers(self):
        authorization = await self.get_token()
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {authorization}"
        }

        return headers


    async def fetch_user(self, user: Union[str, int]) -> User:
        autorization = await self.get_token()
        headers = {
            "Content-Type": "application/json",
            "Accept":"application/json",
            "Authorization": f'Bearer {autorization}'
        }

        params = {
            "limit":5
        }
        async with self.session.get(self.API_URL+f"/users/{user}",headers=headers,params=params) as response:
            json = await response.json()


        return User(json)

    async def fetch_user_recent(self, user: Union[str, int]):
        autorization = await self.get_token()
        headers = {
            "Content-Type": "application/json",
            "Accept":"application/json",
            "Authorization": f'Bearer {autorization}'
        }

        params = {
            "limit":5
        }
        async with self.session.get(self.API_URL+f"/users/{user}/scores/recent",headers=headers,params=params) as response:
            json = await response.json()

    

        return json

    async def fetch_user_beatmaps(self, user: str, type: str, limit: int) -> Beatmap:
        autorization = await self.get_token()
        headers = {
            "Content-Type": "application/json",
            "Accept":"application/json",
            "Authorization": f'Bearer {autorization}'
        }

        params = {
            "limit":limit
        }
        if type not in self.beatmap_types:
            types = ', '.join(self.beatmap_types)
            return f"Beatmap type must be in {types}"

        async with self.session.get(self.API_URL+f"/users/{user}/beatmapsets/{type}",headers=headers,params=params) as response:
            json = await response.json()
        
    
        return json
    
    async def tests(self, method: str, /, endpoint: str, params: dict):
        authorization = await self.get_token()
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {authorization}"
        }

        async with self.session.request(method, self.API_URL + endpoint, params=params, headers=headers) as resp:
            json = await resp.json()

        return json

    async def get_beatmap(self, beatmap: Union[str, int]): 
        headers = await self.make_headers()
        params = {

        }

        async with self.session.get(self.API_URL+f"/beatmaps/{beatmap}", headers=headers, params=params) as resp:
            json = await resp.json()

        if 'error' in json.keys():
            raise NoBeatMapFound("No beatmap was found by that ID!")

        return Beatmap(json)


class User:
    def __init__(self, data):
        try:
            self.data = data
            self.username = data.get('username')
            self.global_rank = data.get('statistics').get("global_rank") if data.get('statistics').get("global_rank") is not None else 0
            self.pp = data.get("statistics").get("pp")  if data.get('statistics') else "None"
            self._rank = data.get("statistics").get("grade_counts") if data.get('statistics') else "None"
            self.accuracy = f"{data.get('statistics').get('hit_accuracy'):,.2f}"  if data.get('statistics') else "None"
            self.country_rank = data.get('statistics').get("country_rank") if data.get('statistics').get("country_rank") is not None else 0
            self._profile_order = data['profile_order'] if data['profile_order'] != KeyError else "Cant Get Profile Order!"
            self.country_emoji = f":flag_{data.get('country_code').lower()}:" if data.get("country_code") else "None"
            self.country_code = data.get("country_code") if data.get("country_code") else "None"
            self._country = data.get("country")
            self.avatar_url = data.get("avatar_url")
            self.id = data.get("id")
            self.playstyle = data.get("playstyle") 
            self.playmode = data.get("playmode")
            self.max_combo = data.get("statistics").get("maximum_combo")
            self.level = data.get("statistics").get("level")
            self.follower_count = data.get("follower_count")
            self.total_hits = data.get("statistics").get("total_hits")
            self.total_score = data.get("statistics").get("total_score")
            self.play_count = data.get("statistics").get("play_count")


        except: # These return None if not available so bare except works fine here.
            raise NoUserFound("No user was found by that name!")

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} username: {self.username!r}, id: {self.id}>"

    def __str__(self) -> str:
        return self.username


    @property
    def profile_order(self) -> str:
        profile_order ='\n ​ ​ ​ ​ ​ ​ ​ ​  - '.join(x for x in self._profile_order)
        return profile_order.replace("_", " ")

    @property
    def ranks(self) -> str:
        ss_text = self._rank['ss']
        ssh_text = self._rank['ssh']
        s_text = self._rank['s']
        sh_text = self._rank['sh']
        a_text = self._rank['a']
        return f"``SS {ss_text}`` | ``SSH {ssh_text}`` | ``S {s_text}`` | ``SH {sh_text}`` | ``A {a_text}``"

    @property
    def joined_at(self) -> str:
        if self.data.get("join_date"):
           return date(datetime.datetime.strptime(self.data.get('join_date'), '%Y-%m-%dT%H:%M:%S+00:00').timestamp(), ago=True)

    @property
    def country(self):
        return [self._country['code'], self._country['name']]

    @property
    def raw(self) -> Dict[str, any]:
        return self.data

class Beatmap:
    def __init__(self, data):
        self.data = data
        self.artist = data['beatmapset']['artist']
        self.title = data['beatmapset']['title']
        self.beatmapset = data['beatmapset']
        self.beatmapset_id = data['beatmapset_id']
        self.difficulty_rating = data['difficulty_rating']
        self.id = data['id']
        self.mode = data['mode']
        self.status = data['status']
        self.difficulty = data['version']
        self.cs = data['cs']
        self.drain = data['drain']
        self.last_updated = data['last_updated'].replace('Z', '')
        self.pass_count = data['passcount']
        self.play_count = data['playcount']
        self.url = data['url']    
        self.favorite_count = data['beatmapset']['favourite_count']
        self.nsfw = data['beatmapset']['nsfw']
        self.ranked_date = data['beatmapset']['ranked_date'].replace('Z', '')
        self.submitted_date = data['beatmapset']['submitted_date'].replace('Z', '')
        self.max_combo = data['max_combo']
        self.creator = data['beatmapset']['creator']
        self.ar = data['ar']
        self.bpm = data['bpm']

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} title: {self.title!r}, artist: {self.artist!r}>"

    def covers(self, cover: str) -> str:
        if cover not in self.data['beatmapset']['covers']:
            return "Cover not in covers"

        cover_data = self.data['beatmapset']['covers'][cover]
        return cover_data