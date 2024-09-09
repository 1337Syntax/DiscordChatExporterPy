import discord

from chat_exporter.ext import ParseMode, convert_emoji, custom_emoji, emoji, fill_out


class Reaction:
    """The Reaction Converter"""

    @staticmethod
    async def flow(guild: discord.Guild, *, reaction: discord.Reaction) -> str:
        if reaction.is_custom_emoji():
            assert isinstance(reaction.emoji, (discord.Emoji, discord.PartialEmoji))
            return await fill_out(
                guild, custom_emoji, [
                    ("EMOJI", str(reaction.emoji.id), ParseMode.NONE),
                    ("EMOJI_COUNT", str(reaction.count), ParseMode.NONE),
                    ("EMOJI_FILE", "gif" if reaction.emoji.animated else "png", ParseMode.NONE),
                ],
            )
        else:
            return await fill_out(
                guild, emoji, [
                    ("EMOJI", await convert_emoji(str(reaction.emoji)), ParseMode.NONE),
                    ("EMOJI_COUNT", str(reaction.count), ParseMode.NONE),
                ],
            )
