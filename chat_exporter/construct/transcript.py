import discord

import html
import pytz
import re
import traceback
from datetime import datetime

from typing import Any, Dict, List, Optional

from ..construct import AttachmentHandler, Component, gather_messages
from ..ext import (
    DiscordIcons,
    ParseMode,
    channel_subject,
    channel_topic,
    clear_cache,
    fill_out,
    meta_data_temp,
    total,
)
from ..parse import ParseMarkdown, pass_bot


class TranscriptDAO:
    """The Transcript Data Access Object"""

    html: str

    def __init__(
        self,
        channel: discord.abc.Messageable,
        limit: Optional[int],
        messages: Optional[List[discord.Message]],
        military_time: bool,
        before: Optional[datetime],
        after: Optional[datetime],
        bot: Optional[discord.Client],
        attachment_handler: Optional[Any],
    ):
        self.channel = channel
        self.messages = messages
        self.limit = limit
        self.military_time = military_time
        self.before = before
        self.after = after
        self.bot = bot

        if attachment_handler and not isinstance(attachment_handler, AttachmentHandler):
            raise TypeError(
                "'attachment_handler' Must be an Instance of AttachmentHandler",
            )
        self.attachment_handler = attachment_handler

        if self.bot:
            pass_bot(self.bot)

    @property
    def time_format(self) -> str:
        return "%A, %d %B %Y %H:%M" if self.military_time else "%A, %d %B %Y %I:%M %p"

    @property
    def guild(self) -> Optional[discord.Guild]:
        if isinstance(self.channel, (discord.Thread, discord.abc.GuildChannel)):
            return self.channel.guild
        else:
            return None

    @property
    def channel_name(self) -> str:
        if isinstance(self.channel, (discord.Thread, discord.abc.GuildChannel)):
            return html.escape(self.channel.name)
        elif isinstance(self.channel, discord.GroupChannel):
            return " ".join(
                [html.escape(user.name) for user in self.channel.recipients],
            )
        elif isinstance(self.channel, discord.DMChannel):
            if self.channel.recipient:
                return html.escape(self.channel.recipient.name)
            else:
                return html.escape("DM Channel")
        else:
            raise TypeError("Channel Type is Not Supported")

    @property
    def channel_icon(self) -> str:
        if isinstance(self.channel, discord.abc.GuildChannel):
            if self.channel.guild.icon:
                return self.channel.guild.icon.url
        elif isinstance(self.channel, discord.abc.PrivateChannel):
            if isinstance(self.channel, discord.GroupChannel):
                if self.channel.icon:
                    return self.channel.icon.url
            elif isinstance(self.channel, discord.DMChannel):
                if (self.channel.recipient) and (self.channel.recipient.avatar):
                    return self.channel.recipient.avatar.url
        return DiscordIcons.default_avatar

    async def build_transcript(self):
        assert self.messages is not None

        message_html, meta_data = await gather_messages(
            self.messages,
            self.guild,
            self.military_time,
            self.attachment_handler,
        )
        await self.export_transcript(message_html, meta_data)
        clear_cache()
        Component.MENU_DIV_ID = 0
        ParseMarkdown.CODE_BLOCK_CONTENT = {}
        return self

    async def export_transcript(self, message_html: str, meta_data: Dict[int, List[Any]]) -> None:
        assert self.messages is not None

        meta_data_html: str = ""
        for data in meta_data:
            creation_time: str = meta_data[int(data)][1].isoformat()
            joined_time: str = (
                meta_data[int(data)][5].isoformat()
                if meta_data[int(data)][5] else ""
            )

            pattern = r'^#\d{4}'
            discrim = str(meta_data[int(data)][0][-5:])
            user = str(meta_data[int(data)][0])

            if self.guild:
                guild_data = f'<div class="meta__divider"></div>\n<img src="{str(self.channel_icon)}" class="meta__img-border" /> <span data-timestamp="{str(joined_time)}"></span>'
            else:
                guild_data = ""

            meta_data_html += await fill_out(
                self.guild, meta_data_temp, [
                    ("USER_ID", str(data), ParseMode.NONE),
                    (
                        "USERNAME", user[:-5] if re.match(pattern, discrim)
                        else user, ParseMode.NONE,
                    ),
                    ("DISCRIMINATOR", discrim if re.match(pattern, discrim) else ""),
                    ("BOT", str(meta_data[int(data)][2]), ParseMode.NONE),
                    ("CREATED_AT", str(creation_time), ParseMode.NONE),
                    ("JOINED_AT", str(joined_time), ParseMode.NONE),
                    ("GUILD_JOINED_AT", str(guild_data), ParseMode.NONE),
                    ("DISCORD_ICON", str(DiscordIcons.logo), ParseMode.NONE),
                    ("MEMBER_ID", str(data), ParseMode.NONE),
                    ("USER_AVATAR", str(meta_data[int(data)][3]), ParseMode.NONE),
                    ("DISPLAY", str(meta_data[int(data)][6]), ParseMode.NONE),
                    ("MESSAGE_COUNT", str(meta_data[int(data)][4])),
                ],
            )

        channel_creation_time = self.channel.created_at.isoformat()  # type: ignore

        raw_channel_topic = (
            self.channel.topic
            if isinstance(self.channel, discord.TextChannel) and self.channel.topic else ""
        )

        channel_topic_html = ""
        if raw_channel_topic:
            channel_topic_html = await fill_out(
                self.guild, channel_topic, [
                    ("CHANNEL_TOPIC", html.escape(raw_channel_topic)),
                ],
            )

        if self.limit:
            limit = f"latest {self.limit} messages"
        else:
            if isinstance(self.channel, (discord.Thread, discord.abc.GuildChannel)):
                limit = "start"
                ending = f"the #{self.channel_name}"
                if isinstance(self.channel, discord.Thread):
                    ending += " thread"
                else:
                    ending += " channel"
            else:
                limit = "beginning"
                if isinstance(self.channel, discord.GroupChannel):
                    ending = f"the {self.channel_name} group"
                else:
                    ending = f"your direct message history with {self.channel_name}"

        subject = await fill_out(
            self.guild, channel_subject, [
                ("LIMIT", limit, ParseMode.NONE),
                ("ENDING", ending, ParseMode.NONE),
            ],
        )

        if self.military_time:
            time_format = "HH:mm"
        else:
            time_format = "hh:mm A"

        if isinstance(self.channel, discord.Thread):
            channel_icon = DiscordIcons.thread_channel_icon
        else:
            channel_icon = DiscordIcons.channel_icon

        if isinstance(self.channel, (discord.Thread, discord.abc.GuildChannel)):
            title = f"{self.channel.guild.name}: #{self.channel.name}"
            guild_id = self.channel.guild.id
            server_name = self.channel.guild.name
            intro = f"Welcome to {self.channel.name}"
            channel_type = "Thread" if isinstance(
                self.channel, discord.Thread,
            ) else "Channel"
            context = f"{channel_type} #{self.channel.name} ({self.channel.id}) in Server {self.channel.guild.name} ({self.channel.guild.id})"
        else:
            title = self.channel_name
            server_name = self.channel_name
            guild_id = "N/A"
            intro = self.channel_name
            if isinstance(self.channel, discord.GroupChannel):
                channel_type = "Group"
                context = f"Group {self.channel.name if self.channel.name else self.channel_name} ({self.channel.id})"
            else:
                channel_type = "DM"
                # type: ignore
                context = f"DM with {self.channel_name} ({self.channel.id})"

        self.html = await fill_out(
            self.guild, total, [
                ("TITLE", title, ParseMode.NONE),
                ("CONTEXT", context, ParseMode.NONE),
                ("SERVER_NAME", server_name, ParseMode.NONE),
                ("GUILD_ID", str(guild_id), ParseMode.NONE),
                ("SERVER_AVATAR_URL", str(self.channel_icon), ParseMode.NONE),
                ("MESSAGE_COUNT", str(len(self.messages))),
                ("MESSAGES", message_html, ParseMode.NONE),
                ("META_DATA", meta_data_html, ParseMode.NONE),
                ("DATE_TIME", datetime.now(pytz.timezone("UTC")).isoformat(), ParseMode.NONE),
                ("SUBJECT", subject, ParseMode.NONE),
                ("CHANNEL_TITLE", intro, ParseMode.NONE),
                ("CHANNEL_NAME", self.channel_name, ParseMode.NONE),
                ("CHANNEL_CREATED_AT", str(channel_creation_time), ParseMode.NONE),
                ("CHANNEL_TOPIC", str(channel_topic_html), ParseMode.NONE),
                ("CHANNEL_ID", str(self.channel.id), ParseMode.NONE),  # type: ignore
                ("CHANNEL_ICON", channel_icon, ParseMode.NONE),
                ("CHANNEL_TYPE", channel_type, ParseMode.NONE),
                ("MESSAGE_PARTICIPANTS", str(len(meta_data)), ParseMode.NONE),
                ("TIME_FORMAT", time_format, ParseMode.NONE),
            ],
            finalise=True,
        )


class Transcript(TranscriptDAO):
    """The Transcript Builder"""

    async def export(self) -> Optional[TranscriptDAO]:
        if not self.messages:
            self.messages = [
                message async for message in self.channel.history(
                    limit=self.limit,
                    before=self.before,
                    after=self.after,
                    oldest_first=True if self.after is None else False,
                )
            ]

        fetch = False
        if isinstance(self.channel, discord.abc.PrivateChannel):
            if isinstance(self.channel, discord.GroupChannel):
                if not self.channel.recipients:
                    fetch = True
            elif isinstance(self.channel, discord.DMChannel):
                if not self.channel.recipient:
                    fetch = True

        if (fetch) and (self.bot):
            try:
                channel: discord.abc.Messageable = await self.bot.fetch_channel(
                    self.channel.id,  # type: ignore
                )
            except discord.HTTPException:
                pass
            else:
                self.channel = channel

        try:
            return await super().build_transcript()
        except Exception:
            traceback.print_exc()
            print("An Un-Expected Error has Occurred!\nPlease Create a Bug Report & Send the Above Here: https://github.com/1337Syntax/DiscordChatExporterPy/issues")
            return None
