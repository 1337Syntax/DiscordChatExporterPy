import discord

import os
from enum import Enum

from typing import List, Optional, Tuple, Union

from ..parse import ParseMarkdown, ParseMention

dir_path = os.path.abspath(
    os.path.join(
        (os.path.dirname(os.path.realpath(__file__))), "..",
    ),
)


class ParseMode(Enum):
    NONE = 0
    NO_MARKDOWN = 1
    MARKDOWN = 2
    EMBED = 3
    SPECIAL_EMBED = 4
    REFERENCE = 5
    EMOJI = 6


async def fill_out(guild: Optional[discord.Guild], base: str, replacements: List[Union[Tuple[str, str], Tuple[str, str, ParseMode]]], *, finalise: bool = False) -> str:
    for r in replacements:
        if len(r) == 2:
            k, v = r
            r = (k, v, ParseMode.MARKDOWN)

        k, v, mode = r

        if mode != ParseMode.NONE:
            v = await ParseMention.flow(guild, content=v)

        if mode == ParseMode.MARKDOWN:
            v = await ParseMarkdown(v).standard_message_flow()
        elif mode == ParseMode.EMBED:
            v = await ParseMarkdown(v).standard_embed_flow()
        elif mode == ParseMode.SPECIAL_EMBED:
            v = await ParseMarkdown(v).special_embed_flow()
        elif mode == ParseMode.REFERENCE:
            v = await ParseMarkdown(v).message_reference_flow()
        elif mode == ParseMode.EMOJI:
            v = await ParseMarkdown(v).special_emoji_flow()

        base = base.replace("{{" + k + "}}", v.strip())

    if finalise:
        base = ParseMarkdown.reverse_code_block_markdown(base)

    return base


def read_file(filename: str) -> str:
    with open(filename, "r") as f:
        s = f.read()
    return s


# MESSAGES
start_message = read_file(dir_path + "/html/message/start.html")
app_tag = read_file(dir_path + "/html/message/app-tag.html")
app_tag_verified = read_file(dir_path + "/html/message/app-tag-verified.html")
message_content = read_file(dir_path + "/html/message/content.html")
message_reference = read_file(dir_path + "/html/message/reference.html")
message_interaction = read_file(dir_path + "/html/message/interaction.html")
message_pin = read_file(dir_path + "/html/message/pin.html")
message_thread = read_file(dir_path + "/html/message/thread.html")
message_thread_remove = read_file(dir_path + "/html/message/thread_remove.html")
message_thread_add = read_file(dir_path + "/html/message/thread_add.html")
message_reference_unknown = read_file(dir_path + "/html/message/reference_unknown.html")
message_body = read_file(dir_path + "/html/message/message.html")
end_message = read_file(dir_path + "/html/message/end.html")
meta_data_temp = read_file(dir_path + "/html/message/meta.html")

# COMPONENTS
component_button = read_file(dir_path + "/html/component/component_button.html")
component_menu = read_file(dir_path + "/html/component/component_menu.html")
component_menu_options = read_file(
    dir_path + "/html/component/component_menu_options.html",
)
component_menu_options_emoji = read_file(
    dir_path + "/html/component/component_menu_options_emoji.html",
)

# EMBED
embed_body = read_file(dir_path + "/html/embed/body.html")
embed_title = read_file(dir_path + "/html/embed/title.html")
embed_description = read_file(dir_path + "/html/embed/description.html")
embed_field = read_file(dir_path + "/html/embed/field.html")
embed_field_inline = read_file(dir_path + "/html/embed/field-inline.html")
embed_footer = read_file(dir_path + "/html/embed/footer.html")
embed_footer_icon = read_file(dir_path + "/html/embed/footer_image.html")
embed_image = read_file(dir_path + "/html/embed/image.html")
embed_thumbnail = read_file(dir_path + "/html/embed/thumbnail.html")
embed_author = read_file(dir_path + "/html/embed/author.html")
embed_author_icon = read_file(dir_path + "/html/embed/author_icon.html")

# REACTION
emoji = read_file(dir_path + "/html/reaction/emoji.html")
custom_emoji = read_file(dir_path + "/html/reaction/custom_emoji.html")

# ATTACHMENT
img_attachment = read_file(dir_path + "/html/attachment/image.html")
msg_attachment = read_file(dir_path + "/html/attachment/message.html")
audio_attachment = read_file(dir_path + "/html/attachment/audio.html")
video_attachment = read_file(dir_path + "/html/attachment/video.html")

# GUILD / FULL TRANSCRIPT
total = read_file(dir_path + "/html/base.html")

# SCRIPT
channel_topic = read_file(dir_path + "/html/script/channel_topic.html")
channel_subject = read_file(dir_path + "/html/script/channel_subject.html")
