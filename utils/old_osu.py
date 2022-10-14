from __future__ import annotations
import datetime
import logging
from typing import Dict, List, Union
import aiohttp
from .default import date
from .osu_errors import *

logger = logging.getLogger(__name__)

class Osu:
    def __init__(self, *, client_id: int, client_secret: str, session: aiohttp.ClientSession):
        self.id = client_id
        self.secret = client_secret
        self.session: aiohttp.ClientSession = session
        self.API_URL = "https://osu.ppy.sh/api/v2"
        self.TOKEN_URL = "https://osu.ppy.sh/oauth/token"
        self.beatmap_types = ['favourite', 'graveyard', 'loved', 'most_played', 'pending', 'ranked']
        self.special_types = ['most_played']
        self.score_types = ['best', 'firsts', 'recent']
    
    async def _request(self, method: str, url: str, **kwargs):
        async with self.session.request(method, url,**kwargs) as resp:
            json = await resp.json()

        return json
    async def get_token(self):
        data = {
            "client_id": self.id,
            "client_secret": self.secret,
            'grant_type':'client_credentials',
            'scope':"public",
        }

        async with self.session.post(self.TOKEN_URL,data=data) as response:
            return (await response.json())['access_token']
    
    async def make_headers(self):
        authorization = await self.get_token()
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {authorization}"
        }

        return headers

    async def fetch_user(self, user: Union[str, int]) -> User:
        headers = await self.make_headers()

        params = {
            "limit":5
        }
        json = await self._request("GET", url=self.API_URL+f"/users/{user}", headers=headers, params=params)

        if 'error' in json.keys() and json['error'] is None:
            raise NoUserFound("No user was found by that name!")

        return TestUser(json)

    async def tests(self, method: str, /, endpoint: str, params: dict = None):
        headers = await self.make_headers()
        async with self.session.request(method, self.API_URL + endpoint, params=params, headers=headers) as resp:
            json = await resp.json()

        return json

    async def fetch_user_score(self, user: Union[str, int], /, type: str, limit: int = 1, include_fails: bool = False):
        if type not in self.score_types:
            types = ', '.join(self.score_types)
            raise WrongType(f"Score type must be in {types}")

        headers = await self.make_headers()

        params = {
            "limit": limit,
            "include_fails": f"{0 if include_fails is not True else 1}"
        }

        async with self.session.get(self.API_URL+f"/users/{user}/scores/{type}", headers=headers, params=params) as response:
            json = await response.json()

        beatmaps = []

        for beatmap in json:
            beatmaps.append(Score(beatmap))

        return beatmaps

    async def fetch_user_beatmaps(self, /, user: str, type: str, limit: int) -> List[Beatmapset]:
        headers = await self.make_headers()
        params = {
            "limit": limit
        }
        
        if type not in self.beatmap_types:
            types = ', '.join(self.beatmap_types)
            raise WrongType(f"Beatmap type must be in {types}")

        async with self.session.get(self.API_URL + f"/users/{user}/beatmapsets/{type}",headers=headers,params=params) as response:
            json = await response.json()
    
        beatmaps = []
        
        for beatmap in json:
            if type in self.special_types:
                beatmaps.append(Beatmapset(beatmap['beatmapset']))
            else:
                beatmaps.append(Beatmapset(beatmap))
                
        return beatmaps
    
    async def get_beatmap(self, beatmap: Union[str, int]): 
        headers = await self.make_headers()

        async with self.session.get(self.API_URL+f"/beatmaps/{beatmap}", headers=headers) as resp:
            json = await resp.json()

        if 'error' in json.keys():
            raise NoBeatMapFound("No beatmap was found by that ID!")

        return Beatmap(json)


class _BaseUser:
    __slots__ = (
        "username",
        "id",
        "is_bot",
        "avatar_url"
    )
    def __init__(self, data: dict):
        self._upate(data)

    def _update(self, data: dict):
        self.username = data['username']
        self.id = data['id']
        self.is_bot = data['is_bot']
        self.avatar_url = data['avatar_url']


class TestUser(_BaseUser):
    def __init__(self, data: dict):
        super().__init__(data)
        self.discord = data['discord']



class User:
    def __init__(self, data):
        self.data = data
        self.username = data['username']
        self.global_rank = data.get('statistics').get("global_rank") if data.get('statistics').get("global_rank") is not None else 0
        self.pp = data.get("statistics").get("pp")  if data.get('statistics') else "None"
        self._rank = data.get("statistics").get("grade_counts") if data.get('statistics') else "None"
        self.accuracy = f"{data.get('statistics').get('hit_accuracy'):,.2f}"  if data.get('statistics') else "None"
        self.country_rank = data.get('statistics').get("country_rank") if data.get('statistics').get("country_rank") is not None else 0
        self._profile_order = data['profile_order'] if data['profile_order'] else "Cant Get Profile Order!"
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
        return f"``SS {ss_text:,}`` | ``SSH {ssh_text:,}`` | ``S {s_text:,}`` | ``SH {sh_text:,}`` | ``A {a_text:,}``"

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
        self.last_updated = datetime.datetime.fromisoformat(data['last_updated'].replace('Z', '')) if data['last_updated'] else None
        self.pass_count = data['passcount']
        self.play_count = data['playcount']
        self.url = data['url']    
        self.favorite_count = data['beatmapset']['favourite_count']
        self.nsfw = data['beatmapset']['nsfw']
        self.ranked_date = datetime.datetime.fromisoformat(data['beatmapset']['ranked_date'].replace('Z', '')) if data['beatmapset']['ranked_date'] else None
        self.submitted_date = datetime.datetime.fromisoformat(data['beatmapset']['submitted_date'].replace('Z', ''))  if data['beatmapset']['submitted_date'] else None
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

class BeatmapCompact:
    __slots__ = (
        "beatmapset_id",
        "difficulty_rating",
        "id",
        "mode",
        "status",
        "total_length",
        "user_id",
        "version"
    )
    def __init__(self, data: dict):
        keys = {k: v for k, v in data.items() if k in self.__slots__}
        for k,v in keys.items():
            setattr(self, k, v)
            continue



class Beatmapset:
    __slots__ = (
        "artist",
        "artist_unicode",
        "creator",
        "favourite_count",
        "hype",
        "id",
        "nsfw",
        "offset",
        "play_count",
        "preview_url",
        "source",
        "spotlight",
        "status",
        "title",
        'title_unicode',
        "track_id",
        "user_id",
        "video",
    )

    def __init__(self, data: dict):
        keys = {k: v for k, v in data.items() if k in self.__slots__}
        for k,v in keys.items():
            setattr(self, k, v)
            continue

        self.data = data

    def covers(self, cover: str) -> str:
        if cover not in self.data['covers']:
            covers = ', '.join(self.data['covers'])
            return f"Cover not in covers!\nChoose from {covers}"

        cover_data = self.data['covers'][cover]
        return cover_data

class Score:
    def __init__(self, data: dict):
        keys = {k: v for k, v in data.items()}
        for k, v in keys.items():
            setattr(self, k, v)
            continue

        self.beatmapset = Beatmapset(data['beatmapset'])
        self.beatmap = BeatmapCompact(data['beatmap'])