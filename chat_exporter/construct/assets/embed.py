import discord

import html

from typing import Optional

from ...ext import (
    ParseMode,
    embed_author,
    embed_author_icon,
    embed_body,
    embed_description,
    embed_field,
    embed_field_inline,
    embed_footer,
    embed_footer_icon,
    embed_image,
    embed_thumbnail,
    embed_title,
    fill_out,
)


class Embed:
    """The Embed Converter"""

    @staticmethod
    async def flow(guild: Optional[discord.Guild], *, embed: discord.Embed) -> str:
        if embed.colour:
            r, g, b = embed.colour.to_rgb()
        else:
            r, g, b = 0x20, 0x22, 0x25

        title = html.escape(embed.title) if embed.title else ""
        if title:
            title = await fill_out(
                guild, embed_title, [
                    ("EMBED_TITLE", title, ParseMode.MARKDOWN),
                ],
            )

        description = html.escape(embed.description) if embed.description else ""
        if description:
            description = await fill_out(
                guild, embed_description, [
                    ("EMBED_DESC", description, ParseMode.EMBED),
                ],
            )

        fields = ""
        for field in embed.fields:
            name = html.escape(field.name)  # type: ignore
            value = html.escape(field.value)  # type: ignore
            if field.inline:
                fields += await fill_out(
                    guild, embed_field_inline, [
                        ("FIELD_NAME", name, ParseMode.SPECIAL_EMBED),
                        ("FIELD_VALUE", value, ParseMode.EMBED),
                    ],
                )
            else:
                fields += await fill_out(
                    guild, embed_field, [
                        ("FIELD_NAME", name, ParseMode.SPECIAL_EMBED),
                        ("FIELD_VALUE", value, ParseMode.EMBED),
                    ],
                )

        author = html.escape(
            embed.author.name,
        ) if embed.author and embed.author.name else ""
        if embed.author.name and embed.author.url:
            author = f'<a class="chatlog__embed-author-name-link" href="{embed.author.url}">{author}</a>'
        author_icon = await fill_out(
            guild, embed_author_icon, [
                ("AUTHOR", author, ParseMode.NONE),
                ("AUTHOR_ICON", embed.author.icon_url, ParseMode.NONE),
            ],
        ) if embed.author and embed.author.icon_url else ""
        if author_icon == "" and author != "":
            author = await fill_out(guild, embed_author, [("AUTHOR", author, ParseMode.NONE)])
        else:
            author = author_icon

        image = await fill_out(
            guild, embed_image, [
                ("EMBED_IMAGE", str(embed.image.proxy_url), ParseMode.NONE),
            ],
        ) if embed.image and embed.image.url else ""

        thumbnail = await fill_out(
            guild, embed_thumbnail, [
                ("EMBED_THUMBNAIL", str(embed.thumbnail.url), ParseMode.NONE),
            ],
        ) if embed.thumbnail and embed.thumbnail.url else ""

        if embed.timestamp:
            timestamp = f'<span data-timestamp="{embed.timestamp.isoformat()}""></span>'
        else:
            timestamp = ""

        footer = html.escape(
            embed.footer.text,
        ) if embed.footer and embed.footer.text else ""
        footer_icon = embed.footer.icon_url if embed.footer and embed.footer.icon_url else None

        if footer and timestamp:
            footer = footer + f" {html.escape('•')}  "
        if footer or timestamp:
            if footer_icon:
                footer = await fill_out(
                    guild, embed_footer_icon, [
                        ("EMBED_FOOTER", footer, ParseMode.NONE),
                        ("EMBED_FOOTER_ICON", footer_icon, ParseMode.NONE),
                        ("EMBED_TIMESTAMP", timestamp, ParseMode.NONE),
                    ],
                )
            else:
                footer = await fill_out(
                    guild, embed_footer, [
                        ("EMBED_FOOTER", footer, ParseMode.NONE),
                        ("EMBED_TIMESTAMP", timestamp, ParseMode.NONE),
                    ],
                )

        return await fill_out(
            guild, embed_body, [
                ("EMBED_R", str(r)),
                ("EMBED_G", str(g)),
                ("EMBED_B", str(b)),
                ("EMBED_AUTHOR", author, ParseMode.NONE),
                ("EMBED_TITLE", title, ParseMode.NONE),
                ("EMBED_IMAGE", image, ParseMode.NONE),
                ("EMBED_THUMBNAIL", thumbnail, ParseMode.NONE),
                ("EMBED_DESC", description, ParseMode.NONE),
                ("EMBED_FIELDS", fields, ParseMode.NONE),
                ("EMBED_FOOTER", footer, ParseMode.NONE),
            ],
        )
