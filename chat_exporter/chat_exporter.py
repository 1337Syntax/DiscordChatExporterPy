import discord

import datetime
import io

from typing import List, Optional, Union

from .construct import (
    AttachmentHandler,
    AttachmentToDiscordChannelHandler,
    AttachmentToLocalFileHostHandler,
    Transcript,
)


async def quick_export(
    channel: discord.abc.Messageable,
    bot: Optional[discord.Client] = None,
) -> Optional[discord.Message]:
    """
    Creates an Export of the Channel & Sends it Back in an Embed

    Parameters
    ----------
    channel: :class:`discord.abc.Messageable`
        The Channel to Export
    bot: Optional[:class:`discord.Client`]
        The Bot Instance to Use for Fetching

    Returns
    -------
    Optional[:class:`discord.Message`]
        The Message of the Export if Successful
    """

    transcript = (
        await Transcript(
            channel=channel,
            limit=None,
            messages=None,
            military_time=True,
            before=None,
            after=None,
            bot=bot,
            attachment_handler=None,
        ).export()
    )
    if not transcript:
        return

    if isinstance(channel, (discord.Thread, discord.abc.GuildChannel)):
        channel_name = channel.name
    else:
        channel_name = str(channel.id)  # type: ignore

    transcript_embed = discord.Embed(
        description=f"**Transcript Name:** transcript-{channel_name}\n\n",
        colour=discord.Colour.blurple(),
    )

    transcript_file = discord.File(
        io.BytesIO(
            transcript.html.encode(),
        ), filename=f"transcript-{channel_name}.html",
    )
    return await channel.send(embed=transcript_embed, file=transcript_file)


async def export(
    channel: Union[discord.TextChannel, discord.Thread],
    limit: Optional[int] = None,
    bot: Optional[discord.Client] = None,
    military_time: bool = True,
    before: Optional[datetime.datetime] = None,
    after: Optional[datetime.datetime] = None,
    attachment_handler: Optional[AttachmentHandler] = None,
) -> Optional[str]:
    """
    Creates a Custom Export of the Channel

    Parameters
    ----------
    channel: Union[:class:`discord.TextChannel` | :class:`discord.Thread`]
        The Channel to Export
    limit: Optional[:class:`int`]
        The Limit of Messages to Capture
    bot: Optional[:class:`discord.Client`]
        The Bot Instance to Use for Fetching
    military_time: Optional[:class:`bool`]
        Whether to Use Military Time
    before: Optional[:class:`datetime.datetime`]
        The Time to Capture Messages Before
    after: Optional[:class:`datetime.datetime`]
        The Time to Capture Messages After
    attachment_handler: Optional[:class:`AttachmentHandler`]
        The Attachment Handler to Use

    Returns
    -------
    Optional[:class:`str`]
        The HTML of the Export
    """

    transcript = await Transcript(
        channel=channel,
        limit=limit,
        messages=None,
        military_time=military_time,
        before=before,
        after=after,
        bot=bot,
        attachment_handler=attachment_handler,
    ).export()
    if not transcript:
        return

    return transcript.html


async def raw_export(
    channel: Union[discord.TextChannel, discord.Thread],
    messages: List[discord.Message],
    bot: Optional[discord.Client] = None,
    military_time: bool = False,
    attachment_handler: Optional[AttachmentHandler] = None,
) -> Optional[str]:
    """
    Creates a Raw Export of the Messages Provided

    Parameters
    ----------
    channel: Union[:class:`discord.TextChannel` | :class:`discord.Thread`]
        The Channel that the Messages are From
    messages: List[:class:`discord.Message`]
        The Messages to Export
    bot: Optional[:class:`discord.Client`]
        The Bot Instance to Use for Fetching
    military_time: Optional[:class:`bool`]
        Whether to Use Military Time
    attachment_handler: Optional[:class:`AttachmentHandler`]
        The Attachment Handler to Use

    Returns
    -------
    Optional[:class:`str`]
        The HTML of the Export
    """

    transcript = await Transcript(
        channel=channel,
        limit=None,
        messages=messages,
        military_time=military_time,
        before=None,
        after=None,
        bot=bot,
        attachment_handler=attachment_handler,
    ).export()
    if not transcript:
        return

    return transcript.html


async def quick_link(
    channel: Union[discord.TextChannel, discord.Thread],
    message: discord.Message,
) -> discord.Message:
    """
    Creates a Quick Embed Link for the Transcript File

    Parameters
    ----------
    channel: Union[:class:`discord.TextChannel` | :class:`discord.Thread`]
        The Channel to Send the Link
    message: :class:`discord.Message`
        The Message to Get the Transcript From

    Returns
    -------
    :class:`discord.Message`
        The Message of the Link
    """

    embed = discord.Embed(
        title="Transcript Link",
        description=(
            f"[Click here to view the transcript](https://api.syntax.fo/transcripts/view?url={message.attachments[0].url})"
        ),
        colour=discord.Colour.blurple(),
    )

    return await channel.send(embed=embed)


def link(
    message: discord.Message,
):
    """
    Creates a Link for the Transcript File

    Parameters
    ----------
    message: :class:`discord.Message`
        The Message to Get the Transcript From

    Returns
    -------
    :class:`str`
        The Link (https://api.syntax.fo/transcripts/view?url=ATTACHMENT_URL)
    """

    return "https://api.syntax.fo/transcripts/view?url=" + message.attachments[0].url
