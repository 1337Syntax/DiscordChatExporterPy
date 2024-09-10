import discord

import html
import pytz
import re
import traceback
from datetime import datetime

from typing import Any, Dict, List, Optional

from chat_exporter.construct import AttachmentHandler, Component, gather_messages
from chat_exporter.ext import (
    DiscordIcons,
    ParseMode,
    channel_subject,
    channel_topic,
    clear_cache,
    fill_out,
    meta_data_temp,
    total,
)
from chat_exporter.parse import ParseMarkdown, pass_bot


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

        if attachment_handler and not isinstance(attachment_handler, AttachmentHandler):
            raise TypeError(
                "'attachment_handler' Must be an Instance of AttachmentHandler",
            )
        self.attachment_handler = attachment_handler

        if bot:
            pass_bot(bot)

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
        if isinstance(self.channel, discord.Thread):
            return DiscordIcons.thread_channel_icon
        else:
            return DiscordIcons.channel_icon

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
                guild_data = f'<img src="{str(self.channel_icon)}" class="meta__img-border" /> <span data-timestamp="{str(joined_time)}"></span>'
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
                ending = f"of the #{self.channel_name}"
                if isinstance(self.channel, discord.Thread):
                    ending += " thread"
                else:
                    ending += " channel"
            else:
                limit = "beginning"

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
            channel_type = "Thread" if isinstance(
                self.channel, discord.Thread,
            ) else "Channel"
            context = f"{self.channel.guild.name} ({self.channel.guild.id})"
            guild_id = self.channel.guild.id
            server_name = self.channel.guild.name
            intro = f"Welcome to {self.channel.name}"
        else:
            title = self.channel_name
            channel_type = "Group" if isinstance(
                self.channel, discord.GroupChannel,
            ) else "DM"
            context = ""
            guild_id = "N/A"
            server_name = self.channel_name
            intro = self.channel_name

        self.html = await fill_out(
            self.guild, total, [
                ("TITLE", title, ParseMode.NONE),
                ("CONTEXT", context, ParseMode.NONE),
                ("SERVER_NAME", server_name, ParseMode.NONE),
                ("GUILD_ID", str(guild_id), ParseMode.NONE),
                ("SERVER_AVATAR_URL", str(self.channel_icon), ParseMode.NONE),
                ("CHANNEL_TITLE", intro, ParseMode.NONE),
                ("CHANNEL_NAME", self.channel_name, ParseMode.NONE),
                ("MESSAGE_COUNT", str(len(self.messages))),
                ("MESSAGES", message_html, ParseMode.NONE),
                ("META_DATA", meta_data_html, ParseMode.NONE),
                ("DATE_TIME", datetime.now(pytz.timezone("UTC")).isoformat(), ParseMode.NONE),
                ("SUBJECT", subject, ParseMode.NONE),
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

        try:
            return await super().build_transcript()
        except Exception:
            traceback.print_exc()
            print("An Un-Expected Error has Occurred!\nPlease Create a Bug Report & Send the Above Here: https://github.com/1337Syntax/DiscordChatExporterPy/issues")
            return None
