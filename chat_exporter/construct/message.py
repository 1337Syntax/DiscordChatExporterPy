import discord

import html
from datetime import timedelta

from typing import Any, Dict, List, Optional, Tuple, Union

from ..construct import Attachment, AttachmentHandler, Component, Embed, Reaction
from ..ext import (
    DiscordIcons,
    ParseMode,
    app_tag,
    app_tag_verified,
    cache,
    discriminator,
    end_message,
    fill_out,
    img_attachment,
    message_body,
    message_content,
    message_interaction,
    message_pin,
    message_reference,
    message_reference_unknown,
    message_thread,
    message_thread_add,
    message_thread_remove,
    start_message,
)


def _gather_user_bot(author: Union[discord.User, discord.Member]) -> str:
    if author.bot and author.public_flags.verified_bot:
        return app_tag_verified
    elif author.bot:
        return app_tag
    return ""


def _set_edit_at(message_edited_at: str) -> str:
    return f'<span class="chatlog__reference-edited-timestamp" data-timestamp="{message_edited_at}">(edited)</span>'


class MessageConstruct:
    """Constructs the Message"""

    message_html: str = ""

    embeds: str = ""
    reactions: str = ""
    components: str = ""
    attachments: str = ""
    reference: str = ""
    interaction: str = ""

    def __init__(
        self,
        message: discord.Message,
        starter_message: Optional[discord.Message],
        previous_message: Optional[discord.Message],
        military_time: bool,
        guild: Optional[discord.Guild],
        meta_data: Dict[int, List[Any]],
        message_dict: Dict[int, discord.Message],
        attachment_handler: Optional[AttachmentHandler],
    ):
        self.message = message
        self.starter_message = starter_message
        self.previous_message = previous_message
        self.military_time = military_time
        self.guild = guild
        self.message_dict = message_dict
        self.attachment_handler = attachment_handler

        self.message_created_at, self.message_edited_at = self.set_time()
        self.meta_data = meta_data

    @property
    def time_format(self) -> str:
        return "%A, %d %B %Y %H:%M" if self.military_time else "%A, %d %B %Y %I:%M %p"

    async def construct_message(self) -> Tuple[str, Dict[int, List[Any]]]:
        if discord.MessageType.pins_add == self.message.type:
            await self.build_pin()
        elif discord.MessageType.thread_created == self.message.type:
            await self.build_thread()
        elif discord.MessageType.recipient_remove == self.message.type:
            await self.build_thread_remove()
        elif discord.MessageType.recipient_add == self.message.type:
            await self.build_thread_add()
        else:
            await self.build_message()
        return self.message_html, self.meta_data

    async def build_message(self) -> None:
        await self.build_content()
        await self.build_reference()
        await self.build_interaction()
        await self.build_sticker()
        await self.build_assets()
        await self.build_message_template()
        await self.build_meta_data()

    async def build_pin(self) -> None:
        await self.generate_message_divider(channel_audit=True)
        await self.build_pin_template()

    async def build_thread(self) -> None:
        await self.generate_message_divider(channel_audit=True)
        await self.build_thread_template()

    async def build_thread_remove(self) -> None:
        await self.generate_message_divider(channel_audit=True)
        await self.build_remove()

    async def build_thread_add(self) -> None:
        await self.generate_message_divider(channel_audit=True)
        await self.build_add()

    async def build_meta_data(self) -> None:
        user_id = self.message.author.id

        if user_id in self.meta_data:
            self.meta_data[user_id][4] += 1
        else:
            user_name_discriminator = discriminator(self.message.author)
            user_created_at = self.message.author.created_at
            user_bot = _gather_user_bot(self.message.author)
            user_avatar = (
                self.message.author.display_avatar if self.message.author.display_avatar
                else DiscordIcons.default_avatar
            )
            user_joined_at = getattr(self.message.author, "joined_at", None)
            user_display_name = (
                f'<div class="meta__display-name">{self.message.author.display_name}</div>'
                if self.message.author.display_name != self.message.author.name
                else ""
            )
            self.meta_data[user_id] = [
                user_name_discriminator, user_created_at, user_bot, user_avatar, 1, user_joined_at, user_display_name,
            ]

    async def build_content(self) -> None:
        if not self.message.content:
            self.message.content = ""
            return

        if self.message_edited_at:
            self.message_edited_at = _set_edit_at(self.message_edited_at)

        self.message.content = html.escape(self.message.content)
        self.message.content = await fill_out(
            self.guild, message_content, [
                ("MESSAGE_CONTENT", self.message.content, ParseMode.MARKDOWN),
                ("EDIT", self.message_edited_at, ParseMode.NONE),
            ],
        )

    async def build_reference(self) -> None:
        if not self.message.reference:
            return

        referenced_message_id: int = self.message.reference.message_id  # type: ignore

        message = self.message_dict.get(referenced_message_id)
        if not message:
            try:
                message = await self.message.channel.fetch_message(referenced_message_id)
            except (discord.NotFound, discord.HTTPException) as e:
                self.reference = ""
                if isinstance(e, discord.NotFound):
                    self.reference = message_reference_unknown
                return

        is_app = _gather_user_bot(message.author)
        user_colour = await self._gather_user_colour(message.author)

        def get_interaction_status(interaction_message: discord.Message) -> Union[discord.MessageInteraction, discord.MessageInteractionMetadata, None]:
            if hasattr(interaction_message, 'interaction_metadata'):
                return interaction_message.interaction_metadata
            return interaction_message.interaction

        interaction_status = get_interaction_status(message)

        if not message.content and not interaction_status:
            message.content = "Click to see attachment"
        elif not message.content and interaction_status:
            message.content = "Click to see command"

        icon = ""
        if not interaction_status and (message.embeds or message.attachments):
            icon = DiscordIcons.reference_attachment_icon
        elif interaction_status:
            icon = DiscordIcons.interaction_command_icon

        _, message_edited_at = self.set_time(message)

        if message_edited_at:
            message_edited_at = _set_edit_at(message_edited_at)

        safe_content = message.content.replace("\n", "").replace("<br>", "")
        avatar_url = message.author.display_avatar if message.author.display_avatar else DiscordIcons.default_avatar

        self.reference = await fill_out(
            self.guild, message_reference, [
                ("AVATAR_URL", str(avatar_url), ParseMode.NONE),
                ("APP_TAG", is_app, ParseMode.NONE),
                ("NAME_TAG", discriminator(message.author), ParseMode.NONE),
                ("NAME", str(html.escape(message.author.display_name))),
                ("USER_COLOUR", user_colour, ParseMode.NONE),
                ("CONTENT", safe_content, ParseMode.REFERENCE),
                ("EDIT", message_edited_at, ParseMode.NONE),
                ("ICON", icon, ParseMode.NONE),
                ("USER_ID", str(message.author.id), ParseMode.NONE),
                ("MESSAGE_ID", str(self.message.reference.message_id), ParseMode.NONE),
            ],
        )

    async def build_interaction(self) -> None:
        if hasattr(self.message, 'interaction_metadata'):
            if not self.message.interaction_metadata:
                self.interaction = ""
                return

            command = "a slash command"
            user = self.message.interaction_metadata.user
            interaction_id = self.message.interaction_metadata.id

        elif self.message.interaction:
            command = f"/{self.message.interaction.name}"
            user = self.message.interaction.user
            interaction_id = self.message.interaction.id

        else:
            self.interaction = ""
            return

        is_app = _gather_user_bot(user)
        user_colour = await self._gather_user_colour(user)
        avatar_url = user.display_avatar if user.display_avatar else DiscordIcons.default_avatar
        self.interaction = await fill_out(
            self.guild, message_interaction, [
                ("AVATAR_URL", str(avatar_url), ParseMode.NONE),
                ("APP_TAG", is_app, ParseMode.NONE),
                ("NAME_TAG", discriminator(user), ParseMode.NONE),
                ("NAME", str(html.escape(user.display_name))),
                ("USER_COLOUR", user_colour, ParseMode.NONE),
                ("FILLER", "used ", ParseMode.NONE),
                ("COMMAND", str(command), ParseMode.NONE),
                ("USER_ID", str(user.id), ParseMode.NONE),
                ("INTERACTION_ID", str(interaction_id), ParseMode.NONE),
            ],
        )

    async def build_sticker(self) -> None:
        if not self.message.stickers or not hasattr(self.message.stickers[0], "url"):
            return

        sticker = await self.message.stickers[0].fetch()

        if isinstance(sticker, discord.StandardSticker):
            sticker_image_url = (
                f"https://cdn.jsdelivr.net/gh/mahtoid/DiscordUtils@master/stickers/{sticker.pack_id}/{sticker.id}.gif"
            )
        else:
            sticker_image_url = sticker.url

        self.message.content = await fill_out(
            self.guild, img_attachment, [
                ("ATTACH_URL", str(sticker_image_url), ParseMode.NONE),
                ("ATTACH_URL_THUMB", str(sticker_image_url), ParseMode.NONE),
            ],
        )

    async def build_assets(self) -> None:
        for e in self.message.embeds:
            self.embeds += await Embed.flow(
                self.guild, embed=e,
            )

        for a in self.message.attachments:
            if self.attachment_handler:
                a = await self.attachment_handler.process_asset(a)
            self.attachments += await Attachment.flow(
                self.guild, attachment=a,
            )

        for c in self.message.components:
            self.components += await Component.flow(
                self.guild, component=c,
            )

        for r in self.message.reactions:
            self.reactions += await Reaction.flow(
                self.guild, reaction=r,
            )

        if self.reactions:
            self.reactions = f'<div class="chatlog__reactions">{self.reactions}</div>'

    async def build_message_template(self) -> str:
        started = await self.generate_message_divider()

        if started:
            return self.message_html

        self.message_html += await fill_out(
            self.guild, message_body, [
                ("MESSAGE_ID", str(self.message.id)),
                ("MESSAGE_CONTENT", self.message.content, ParseMode.NONE),
                ("EMBEDS", self.embeds, ParseMode.NONE),
                ("ATTACHMENTS", self.attachments, ParseMode.NONE),
                ("COMPONENTS", self.components, ParseMode.NONE),
                ("EMOJI", self.reactions, ParseMode.NONE),
                ("TIMESTAMP", self.message_created_at, ParseMode.NONE),
            ],
        )

        return self.message_html

    def _generate_message_divider_check(self) -> bool:
        return bool(
            self.previous_message is None or self.reference != "" or
            self.previous_message == self.starter_message or
            self.previous_message.type is not discord.MessageType.default or self.interaction != "" or
            self.previous_message.author.id != self.message.author.id or self.message.webhook_id is not None or
            self.message.created_at > (
                self.previous_message.created_at + timedelta(minutes=7)
            ),
        )

    async def generate_message_divider(self, channel_audit: bool = False) -> bool:
        if channel_audit or self._generate_message_divider_check():
            if self.previous_message is not None:
                self.message_html += await fill_out(self.guild, end_message, [])

            if channel_audit:
                self.audit = True
                return False

            followup_symbol = ""
            is_app = _gather_user_bot(self.message.author)
            avatar_url = self.message.author.display_avatar if self.message.author.display_avatar else DiscordIcons.default_avatar

            if self.reference != "" or self.interaction:
                followup_symbol = "<div class='chatlog__followup-symbol'></div>"

            self.message_html += await fill_out(
                self.guild, start_message, [
                    ("REFERENCE_SYMBOL", followup_symbol, ParseMode.NONE),
                    ("REFERENCE", self.reference if self.message.reference else self.interaction, ParseMode.NONE),
                    ("AVATAR_URL", str(avatar_url), ParseMode.NONE),
                    ("NAME_TAG", discriminator(self.message.author), ParseMode.NONE),
                    ("USER_ID", str(self.message.author.id)),
                    ("USER_COLOUR", await self._gather_user_colour(self.message.author)),
                    ("USER_ICON", await self._gather_user_icon(self.message.author), ParseMode.NONE),
                    ("NAME", html.escape(self.message.author.display_name)),
                    ("APP_TAG", is_app, ParseMode.NONE),
                    ("TIMESTAMP", self.message_created_at),
                    ("MESSAGE_ID", str(self.message.id)),
                    ("MESSAGE_CONTENT", self.message.content, ParseMode.NONE),
                    ("EMBEDS", self.embeds, ParseMode.NONE),
                    ("ATTACHMENTS", self.attachments, ParseMode.NONE),
                    ("COMPONENTS", self.components, ParseMode.NONE),
                    ("EMOJI", self.reactions, ParseMode.NONE),
                ],
            )
            return True

        return False

    async def build_pin_template(self) -> None:
        self.message_html += await fill_out(
            self.guild, message_pin, [
                ("PIN_URL", DiscordIcons.pinned_message_icon, ParseMode.NONE),
                ("USER_COLOUR", await self._gather_user_colour(self.message.author)),
                ("NAME", str(html.escape(self.message.author.display_name))),
                ("NAME_TAG", discriminator(self.message.author), ParseMode.NONE),
                ("MESSAGE_ID", str(self.message.id), ParseMode.NONE),
                (
                    "REF_MESSAGE_ID", str(self.message.reference.message_id)
                    if self.message.reference else "", ParseMode.NONE,
                ),
            ],
        )

    async def build_thread_template(self):
        self.message_html += await fill_out(
            self.guild, message_thread, [
                (
                    "THREAD_URL", DiscordIcons.thread_channel_icon,
                    ParseMode.NONE,
                ),
                ("THREAD_NAME", self.message.content, ParseMode.NONE),
                ("USER_COLOUR", await self._gather_user_colour(self.message.author)),
                ("NAME", str(html.escape(self.message.author.display_name))),
                ("NAME_TAG", discriminator(self.message.author), ParseMode.NONE),
                ("MESSAGE_ID", str(self.message.id), ParseMode.NONE),
            ],
        )

    async def build_remove(self) -> None:
        removed_member = self.message.mentions[0]
        self.message_html += await fill_out(
            self.guild, message_thread_remove, [
                ("THREAD_URL", DiscordIcons.thread_remove_recipient, ParseMode.NONE),
                ("USER_COLOUR", await self._gather_user_colour(self.message.author)),
                ("NAME", str(html.escape(self.message.author.display_name))),
                ("NAME_TAG", discriminator(self.message.author), ParseMode.NONE),
                ("RECIPIENT_USER_COLOUR", await self._gather_user_colour(removed_member)),
                ("RECIPIENT_NAME", str(html.escape(removed_member.display_name))),
                ("RECIPIENT_NAME_TAG", discriminator(removed_member), ParseMode.NONE),
                ("MESSAGE_ID", str(self.message.id), ParseMode.NONE),
            ],
        )

    async def build_add(self) -> None:
        removed_member = self.message.mentions[0]
        self.message_html += await fill_out(
            self.guild, message_thread_add, [
                ("THREAD_URL", DiscordIcons.thread_add_recipient, ParseMode.NONE),
                ("USER_COLOUR", await self._gather_user_colour(self.message.author)),
                ("NAME", str(html.escape(self.message.author.display_name))),
                ("NAME_TAG", discriminator(self.message.author), ParseMode.NONE),
                ("RECIPIENT_USER_COLOUR", await self._gather_user_colour(removed_member)),
                ("RECIPIENT_NAME", str(html.escape(removed_member.display_name))),
                ("RECIPIENT_NAME_TAG", discriminator(removed_member), ParseMode.NONE),
                ("MESSAGE_ID", str(self.message.id), ParseMode.NONE),
            ],
        )

    @cache()
    async def _gather_member(self, author: discord.abc.User) -> Optional[discord.Member]:
        if not self.guild:
            return None

        member = self.guild.get_member(author.id)
        if member:
            return member

        try:
            return await self.guild.fetch_member(author.id)
        except Exception:
            return None

    async def _gather_user_colour(self, author: discord.abc.User) -> str:
        member = await self._gather_member(author)
        user_colour = member.colour if member and str(
            member.colour,
        ) != "#000000" else "#FFFFFF"
        return f"color: {user_colour};"

    async def _gather_user_icon(self, author: discord.abc.User) -> str:
        member = await self._gather_member(author)
        if not member:
            return ""

        if hasattr(member, "display_icon") and member.display_icon:
            return f"<img class='chatlog__role-icon' src='{member.display_icon}' alt='Role Icon'>"
        elif hasattr(member, "top_role") and member.top_role and member.top_role.icon:
            return f"<img class='chatlog__role-icon' src='{member.top_role.icon}' alt='Role Icon'>"
        return ""

    def set_time(self, message: Optional[discord.Message] = None) -> Tuple[str, str]:
        message = message if message else self.message
        created_at_str = message.created_at.isoformat()
        edited_at_str = message.edited_at.isoformat() if message.edited_at else ""

        return created_at_str, edited_at_str


async def gather_messages(messages: List[discord.Message], guild: Optional[discord.Guild], military_time: bool, attachment_handler: Optional[AttachmentHandler]) -> Tuple[str, Dict[int, List[Any]]]:
    message_html: str = ""
    meta_data: Dict[int, List[Any]] = {}
    previous_message: Optional[discord.Message] = None
    starter_message: Optional[discord.Message] = None

    message_dict = {message.id: message for message in messages}

    if messages and isinstance(messages[0].channel, discord.Thread) and messages[0].reference:
        starter_message = messages[0].channel.starter_message
        if not starter_message:
            assert guild is not None
            channel: Optional[discord.TextChannel] = messages[0].channel.parent or guild.get_channel(  # type: ignore
                messages[0].channel.parent_id,
            )
            if not channel:
                try:
                    channel = await guild.fetch_channel(
                        messages[0].channel.parent_id,  # type: ignore
                    )
                except discord.NotFound:
                    pass

            if channel:
                try:
                    starter_message = await channel.fetch_message(
                        messages[0].channel.id,
                    )
                except discord.NotFound:
                    pass

        if starter_message:
            messages[0] = starter_message
            messages[0].reference = None

    for message in messages:
        content_html, meta_data = await MessageConstruct(
            message,
            starter_message,
            previous_message,
            military_time,
            guild,
            meta_data,
            message_dict,
            attachment_handler,
        ).construct_message()

        message_html += content_html
        previous_message = message

    message_html += "</div>"
    return message_html, meta_data
