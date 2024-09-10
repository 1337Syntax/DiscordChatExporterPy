import discord

import pytz
import re
from datetime import datetime

from typing import Optional

from chat_exporter.parse import ParseMarkdown

bot: Optional[discord.Client] = None


def pass_bot(_bot: discord.Client) -> None:
    global bot
    bot = _bot


class ParseMention:
    """The Mention Parser"""

    REGEX_ROLES = r"(?<!\\)&lt;@&amp;([0-9]+)&gt;"
    REGEX_ROLES_2 = r"(?<!\\)<@&([0-9]+)>"
    REGEX_EVERYONE = r"(?<!\\)@(everyone)(?:[$\s\t\n\f\r\0]|$)"
    REGEX_HERE = r"(?<!\\)@(here)(?:[$\s\t\n\f\r\0]|$)"
    REGEX_MEMBERS = r"(?<!\\)&lt;@!?([0-9]+)&gt;"
    REGEX_MEMBERS_2 = r"(?<!\\)<@!?([0-9]+)>"
    REGEX_CHANNELS = r"(?<!\\)&lt;#([0-9]+)&gt;"
    REGEX_CHANNELS_2 = r"(?<!\\)<#([0-9]+)>"
    REGEX_EMOJIS = r"(?<!\\)&lt;a?(:[^\n:]+:)[0-9]+&gt;"
    REGEX_EMOJIS_2 = r"(?<!\\)<a?(:[^\n:]+:)[0-9]+>"
    REGEX_TIME_HOLDER = (
        [r"(?<!\\)&lt;t:([0-9]{1,13}):t&gt;"],
        [r"(?<!\\)&lt;t:([0-9]{1,13}):T&gt;"],
        [r"(?<!\\)&lt;t:([0-9]{1,13}):d&gt;"],
        [r"(?<!\\)&lt;t:([0-9]{1,13}):D&gt;"],
        [r"(?<!\\)&lt;t:([0-9]{1,13}):f&gt;"],
        [r"(?<!\\)&lt;t:([0-9]{1,13}):F&gt;"],
        [r"(?<!\\)&lt;t:([0-9]{1,13}):R&gt;"],
        [r"(?<!\\)&lt;t:([0-9]{1,13})&gt;"],
    )
    REGEX_SLASH_COMMAND = r"(?<!\\)&lt;\/([\w\s-]+):[0-9]+&gt;"

    ESCAPE_LT = "______lt______"
    ESCAPE_GT = "______gt______"
    ESCAPE_AMP = "______amp______"

    @staticmethod
    async def flow(guild: Optional[discord.Guild], *, content: str) -> str:
        markdown = ParseMarkdown(content)
        markdown.parse_code_block_markdown()
        content = markdown.content

        for match in re.finditer(
            "(%s|%s|%s|%s|%s|%s|%s|%s)" % (
                ParseMention.REGEX_ROLES,
                ParseMention.REGEX_MEMBERS,
                ParseMention.REGEX_CHANNELS,
                ParseMention.REGEX_EMOJIS,
                ParseMention.REGEX_ROLES_2,
                ParseMention.REGEX_MEMBERS_2,
                ParseMention.REGEX_CHANNELS_2,
                ParseMention.REGEX_EMOJIS_2,
            ), content,
        ):
            pre_content = content[:match.start()]
            post_content = content[match.end():]
            match_content = content[match.start():match.end()]

            match_content = match_content.replace("<", ParseMention.ESCAPE_LT)
            match_content = match_content.replace(">", ParseMention.ESCAPE_GT)
            match_content = match_content.replace("&", ParseMention.ESCAPE_AMP)

            content = pre_content + match_content + post_content

        content = content.replace(ParseMention.ESCAPE_LT, "<")
        content = content.replace(ParseMention.ESCAPE_GT, ">")
        content = content.replace(ParseMention.ESCAPE_AMP, "&")

        for regex in (ParseMention.REGEX_CHANNELS, ParseMention.REGEX_CHANNELS_2):
            match = re.search(regex, content)
            while match is not None:
                if guild:
                    channel_id = int(match.group(1))
                    channel = guild.get_channel(channel_id)
                else:
                    channel = None

                if channel is None:
                    replacement = "#deleted-channel"
                else:
                    replacement = f'<span class="mention" title="{channel.id}">#{channel.name}</span>'

                content = content.replace(
                    content[match.start():match.end()],
                    replacement,
                )
                match = re.search(regex, content)

        for regex in (ParseMention.REGEX_MEMBERS, ParseMention.REGEX_MEMBERS_2):
            match = re.search(regex, content)
            while match is not None:
                if guild:
                    member_id = int(match.group(1))
                    member = guild.get_member(member_id)
                    if not member and bot:
                        member = bot.get_user(member_id) or await bot.fetch_user(member_id)
                else:
                    member = None
                member_name = member.display_name if member else str(member_id)

                replacement = f'<span class="mention" title="{member_id}">@{member_name}</span>'
                content = content.replace(
                    content[match.start():match.end()],
                    replacement,
                )
                match = re.search(regex, content)

        for regex in (ParseMention.REGEX_EVERYONE, ParseMention.REGEX_HERE):
            match = re.search(regex, content)
            while match is not None:
                role_name = match.group(1)
                replacement = f'<span class="mention" title="{role_name}">@{role_name}</span>'
                content = content.replace(
                    content[match.start():match.end()],
                    replacement,
                )
                match = re.search(regex, content)

        for regex in (ParseMention.REGEX_ROLES, ParseMention.REGEX_ROLES_2):
            match = re.search(regex, content)
            while match is not None:
                if guild:
                    role_id = int(match.group(1))
                    role = guild.get_role(role_id)
                else:
                    role = None

                if role is None:
                    replacement = "@deleted-role"
                else:
                    colour = f"#{role.color.value:06x}"
                    replacement = f'<span style="color: {colour};">@{role.name}</span>'

                content = content.replace(
                    content[match.start():match.end()],
                    replacement,
                )
                match = re.search(regex, content)

        for regex in ParseMention.REGEX_TIME_HOLDER:
            r = regex[0]
            match = re.search(r, content)
            while match is not None:
                timestamp = int(match.group(1)) - 1
                tooltip_time = datetime.fromtimestamp(
                    timestamp, tz=pytz.utc,
                ).isoformat()
                original = match.group().replace("&lt;", "<").replace("&gt;", ">")
                key = original[-2]
                if key.isdigit():
                    key = "f"
                else:
                    key = original[-2]

                replacement = f'<span class="unix-timestamp" data-timestamp="{tooltip_time}" data-timestamp-format="{key}" data-timestamp-raw="{original}">{original}</span>'

                content = content.replace(
                    content[match.start():match.end()],
                    replacement,
                )
                match = re.search(r, content)

        for regex in (ParseMention.REGEX_SLASH_COMMAND,):
            match = re.search(regex, content)
            while match is not None:
                slash_command_name = match.group(1)
                replacement = f'<span class="mention" title="{slash_command_name}">/{slash_command_name}</span>'
                content = content.replace(
                    content[match.start():match.end()],
                    replacement,
                )
                match = re.search(regex, content)

        markdown.content = content
        content = markdown.content
        return content
