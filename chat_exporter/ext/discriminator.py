import discord


def discriminator(user: discord.abc.User) -> str:
    """
    Formats the User's Discriminator

    Parameters
    ----------
    user: :class:`discord.abc.User`
        The User to Format the Discriminator

    Returns
    -------
    :class:`str`
        The Formatted Discriminator
    """

    if user.discriminator != "0":
        return f"{user.name}#{user.discriminator}"
    else:
        return str(user)
