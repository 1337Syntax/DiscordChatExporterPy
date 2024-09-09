import discord

import math

from chat_exporter.ext import (
    DiscordIcons,
    ParseMode,
    audio_attachment,
    fill_out,
    img_attachment,
    msg_attachment,
    video_attachment,
)


def get_file_icon(attachment: discord.Attachment) -> str:
    acrobat_types = "pdf"
    webcode_types = "html", "htm", "css", "rss", "xhtml", "xml"
    code_types = "py", "cgi", "pl", "gadget", "jar", "msi", "wsf", "bat", "php", "js"
    document_types = (
        "txt", "doc", "docx", "rtf", "xls", "xlsx", "ppt", "pptx", "odt", "odp", "ods", "odg", "odf", "swx",
        "sxi", "sxc", "sxd", "stw",
    )
    archive_types = (
        "br", "rpm", "dcm", "epub", "zip", "tar", "rar", "gz", "bz2", "7x", "deb", "ar", "Z", "lzo", "lz", "lz4",
        "arj", "pkg", "z",
    )
    extension = attachment.url.rsplit('.', 1)[1]
    if extension in acrobat_types:
        return DiscordIcons.file_attachment_acrobat
    elif extension in webcode_types:
        return DiscordIcons.file_attachment_webcode
    elif extension in code_types:
        return DiscordIcons.file_attachment_code
    elif extension in document_types:
        return DiscordIcons.file_attachment_document
    elif extension in archive_types:
        return DiscordIcons.file_attachment_archive
    else:
        return DiscordIcons.file_attachment_unknown


def get_file_size(file_size: int) -> str:
    if file_size == 0:
        return "0 bytes"

    size_name = ("bytes", "KB", "MB")
    i = int(math.floor(math.log(file_size, 1024)))
    p = math.pow(1024, i)
    s = round(file_size / p, 2)
    return "%s %s" % (s, size_name[i])


class Attachment:
    """The Attachment Converter"""

    @staticmethod
    async def flow(guild: discord.Guild, *, attachment: discord.Attachment) -> str:
        if attachment.content_type is not None:
            if "image" in attachment.content_type:
                return await fill_out(
                    guild, img_attachment, [
                        ("ATTACH_URL", attachment.proxy_url, ParseMode.NONE),
                        ("ATTACH_URL_THUMB", attachment.proxy_url, ParseMode.NONE),
                    ],
                )

            elif "video" in attachment.content_type:
                return await fill_out(
                    guild, video_attachment, [
                        ("ATTACH_URL", attachment.proxy_url, ParseMode.NONE),
                    ],
                )

            elif "audio" in attachment.content_type:
                file_icon = DiscordIcons.file_attachment_audio
                file_size = get_file_size(attachment.size)

                return await fill_out(
                    guild, audio_attachment, [
                        ("ATTACH_ICON", DiscordIcons.file_attachment_audio, ParseMode.NONE),
                        ("ATTACH_URL", attachment.proxy_url, ParseMode.NONE),
                        ("ATTACH_BYTES", str(get_file_size(attachment.size)), ParseMode.NONE),
                        ("ATTACH_AUDIO", attachment.proxy_url, ParseMode.NONE),
                        ("ATTACH_FILE", str(attachment.filename), ParseMode.NONE),
                    ],
                )

        file_icon = get_file_icon(attachment)
        file_size = get_file_size(attachment.size)

        return await fill_out(
            guild, msg_attachment, [
                ("ATTACH_ICON", file_icon, ParseMode.NONE),
                ("ATTACH_URL", attachment.url, ParseMode.NONE),
                ("ATTACH_BYTES", str(file_size), ParseMode.NONE),
                ("ATTACH_FILE", str(attachment.filename), ParseMode.NONE),
            ],
        )
