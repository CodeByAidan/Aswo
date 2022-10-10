import re
error_codes = {
    1:  "emergency stop (triggered manually)", 
    2:  "replay download error (bad upload from the sender) or replay parsing error (bad upload from the sender)", 
    3:  "replay download error (bad download from the server), can happen because of invalid characters",
    4:  "all beatmap mirrors are unavailable",
    5:  "replay file corrupted",
    6:  "invalid osu! gamemode (not 0 = std)",
    7:  "the replay has no input data",
    8:  "This beatmap does not exist on osu!. Custom difficulties or non-submitted maps are not supported.",
    9:  "audio for the map is unavailable (because of copyright claim)",
    10: "cannot connect to osu! api",
    11: "the replay has the autoplay mod",
    12: "the replay username has invalid characters",
    13: "the beatmap is longer than 15 minutes",
    14: "this player is banned from o!rdr",
    15: "beatmap not found on all the beatmap mirrors",
    16: "this IP is banned from o!rdr",
    17: "this username is banned from o!rdr",
    18: "unknown error from the renderer",
    19: "the renderer cannot download the map",
    20: "beatmap version on the mirror is not the same as the replay",
    21: "the replay is corrupted (danser cannot process it)",
    22: "server-side problem while finalizing the generated video",
    23: "server-side problem while preparing the render",
    24: "the beatmap has no name",
    25: "the replay is missing input data",
    26: "the replay has incompatible mods",
    27: "something with the renderer went wrong: it probably has an unstable internet connection (multiple renders at the same time)",
    28: "the renderer cannot download the replay",
    29: "the replay is already rendering or in queue",
    30: "the star rating is greater than 20",
    31: "the mapper is blacklisted",
    32: "the beatmapset is blacklisted",
    33: "the replay has already errored less than an hour ago"
}

URL_RE = re.compile(
    "http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*(),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+osr"
)