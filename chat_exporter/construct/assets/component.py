import discord

from typing import List, Optional

from ...ext import (
    DiscordIcons,
    ParseMode,
    component_button,
    component_menu,
    component_menu_options,
    component_menu_options_emoji,
    fill_out,
)


class Component:
    """The Component Converter"""

    STYLES = {
        discord.ButtonStyle.primary: "#5865F2",
        discord.ButtonStyle.secondary: "#4F545C",
        discord.ButtonStyle.success: "#2D7D46",
        discord.ButtonStyle.danger: "#D83C3E",
        discord.ButtonStyle.blurple: "#5865F2",
        discord.ButtonStyle.grey: "#4F545C",
        discord.ButtonStyle.gray: "#4F545C",
        discord.ButtonStyle.green: "#2D7D46",
        discord.ButtonStyle.red: "#D83C3E",
        discord.ButtonStyle.link: "#4F545C",
    }
    MENU_DIV_ID = 0

    @staticmethod
    async def flow(guild: Optional[discord.Guild], *, component: discord.Component) -> str:
        if isinstance(component, discord.ActionRow):
            buttons = ""
            menus = ""

            for c in component.children:
                if isinstance(c, discord.Button):
                    buttons += await Component.flow(guild, component=c)
                elif isinstance(c, discord.SelectMenu):
                    menus += await Component.flow(guild, component=c)

            return f'<div class="chatlog__components">{buttons}{menus}</div>'

        elif isinstance(component, discord.Button):
            if component.url:
                url = component.url
                target = "target='_blank'"
                icon = DiscordIcons.button_external_link
            else:
                url = "javascript:;"
                target = ""
                icon = ""

            disabled = "chatlog__component-disabled" if component.disabled else ""
            label = component.label or ""
            style = Component.STYLES[component.style]
            emoji = str(component.emoji) if component.emoji else ""

            return await fill_out(
                guild, component_button, [
                    ("DISABLED", disabled, ParseMode.NONE),
                    ("URL", url, ParseMode.NONE),
                    ("LABEL", label, ParseMode.MARKDOWN),
                    ("EMOJI", emoji, ParseMode.EMOJI),
                    ("ICON", icon, ParseMode.NONE),
                    ("TARGET", target, ParseMode.NONE),
                    ("STYLE", style, ParseMode.NONE),
                ],
            )

        elif isinstance(component, discord.SelectMenu):
            Component.MENU_DIV_ID += 1

            disabled = "chatlog__component-disabled" if component.disabled else ""
            placeholder = component.placeholder or ""
            options = component.options
            content = ""

            if not component.disabled:
                contents: List[str] = []
                for option in options:
                    if option.emoji:
                        contents.append(
                            await fill_out(
                                guild, component_menu_options_emoji, [
                                    ("EMOJI", str(option.emoji), ParseMode.EMOJI),
                                    ("TITLE", str(option.label), ParseMode.MARKDOWN),
                                    (
                                        "DESCRIPTION", str(option.description)
                                        if option.description else "", ParseMode.MARKDOWN,
                                    ),
                                ],
                            ),
                        )
                    else:
                        contents.append(
                            await fill_out(
                                guild, component_menu_options, [
                                    ("TITLE", str(option.label), ParseMode.MARKDOWN),
                                    (
                                        "DESCRIPTION", str(option.description)
                                        if option.description else "", ParseMode.MARKDOWN,
                                    ),
                                ],
                            ),
                        )

                if contents:
                    content = f'<div id="dropdownMenu{Component.MENU_DIV_ID}" class="dropdownContent">{"".join(contents)}</div>'

            return await fill_out(
                guild, component_menu, [
                    ("ID", str(Component.MENU_DIV_ID), ParseMode.NONE),
                    ("DISABLED", disabled, ParseMode.NONE),
                    ("PLACEHOLDER", placeholder, ParseMode.MARKDOWN),
                    ("CONTENT", content, ParseMode.NONE),
                    ("ICON", DiscordIcons.interaction_dropdown_icon, ParseMode.NONE),
                ],
            )

        else:
            raise TypeError("Invalid Component Type")
