import discord

import pathlib
import urllib.parse

from typing import Union


class AttachmentHandler:
    """Handles the Saving of Attachments"""

    async def process_asset(self, attachment: discord.Attachment) -> discord.Attachment:
        """
        Returns the Attachment after Processing

        Parameters
        ----------
        attachment: :class:`discord.Attachment`
            The Attachment to Process

        Raises
        ------
        :class:`NotImplementedError`
            This Method Must be Implemented in a Subclass

        Returns
        -------
        :class:`discord.Attachment`
            The Processed Attachment
        """

        raise NotImplementedError


class AttachmentToLocalFileHostHandler(AttachmentHandler):
    """Saves the Attachment Locally"""

    def __init__(self, base_path: Union[str, pathlib.Path], url_base: str) -> None:
        """
        Parameters
        ----------
        base_path: Union[:class:`str`, :class:`pathlib.Path`]
            The Base Path to Save the Attachments
        url_base: :class:`str`
            The Base URL to Access the Attachments
        """

        if isinstance(base_path, str):
            base_path = pathlib.Path(base_path)

        self.base_path = base_path
        self.url_base = url_base

    async def process_asset(self, attachment: discord.Attachment) -> discord.Attachment:
        file_name = urllib.parse.quote_plus(
            f"{attachment.id}_{attachment.filename}", safe="",
        )
        asset_path = self.base_path / file_name
        await attachment.save(asset_path)

        file_url = f"{self.url_base}/{file_name}"
        attachment.url = file_url
        attachment.proxy_url = file_url
        return attachment


class AttachmentToDiscordChannelHandler(AttachmentHandler):
    """Save the Attachment to a Discord Channel"""

    def __init__(self, channel: discord.TextChannel):
        """
        Parameters
        ----------
        channel: :class:`discord.TextChannel`
            The Channel to Save the Attachments
        """

        self.channel = channel

    async def process_asset(self, attachment: discord.Attachment) -> discord.Attachment:
        try:
            file = await attachment.to_file()
            message = await self.channel.send(file=file)
        except discord.HTTPException as E:
            raise E
        else:
            return message.attachments[0]
