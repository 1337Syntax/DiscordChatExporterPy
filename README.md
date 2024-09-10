<div align="center">
   <h1>DiscordChatExporterPy</h1>

   <p>
      A Library to Export your Discord Chats to a HTML File via your Python-Bot!
   </p>
   <p>
      <a href="#installation">Get Started</a>
      •
      <a href="https://github.com/1337Syntax/DiscordChatExporterPy/issues/new?assignees=&labels=bug&template=bug-report.yml">Bug Report</a>
      •
      <a href="https://github.com/1337Syntax/DiscordChatExporterPy/issues/new?assignees=&labels=enhancement&template=feature-request.yml">Request Feature</a>
   </p>
</div>

---

> [!NOTE]
> This Package is Only Usable for [discord.py](https://github.com/Rapptz/discord.py 'discord.py') Bots or Forks that Use the Same Namespace (`discord`), such as [PyCord](https://github.com/Pycord-Development/pycord 'Py-Cord').

<!-- ## Example Output
View a [Live Demo](https://example.com 'Example Transcript') of an Exported Chat Transcript. -->

<br />

## Installation
**Python 3.8 or Higher is Required!**

This Package is NOT Available on PyPI, but You Can Install it via GitHub:

```bash
pip install git+https://github.com/1337Syntax/DiscordChatExporterPy
```

<br />

## Usage
### Creating the Export:
There are 3 Methods Available to Export the Channel:

<details>
   <summary><b>Basic Usage via <code>.quick_export()</code></b></summary>

   > #### Parameters:
   > - channel: `discord.abc.Messageable`
   >    - The Channel to Export
   > - bot: Optional[`discord.Client`]
   >    - The Bot Instance to Use for Fetching
   >
   >
   > #### Returns:
   > - Optional[`discord.Message`]
   >    - The Message of the Export if Successful
   >
   > #### Example:
   > ```python
   > import discord
   > from discord.ext import commands
   >
   > import chat_exporter
   >
   > bot = commands.Bot(...)
   >
   > @bot.command()
   > @commands.guild_only()
   > async def export(ctx: commands.Context):
   >    await chat_exporter.quick_export(ctx.channel, bot)
   > ```
</details>

<details>
   <summary><b>Custom Usage via <code>.export()</code></b></summary>

   > #### Parameters:
   > - channel: `discord.abc.Messageable`
   >    - The Channel to Export
   > - limit: Optional[`int`]
   >    - The Limit of Messages to Capture
   > - bot: Optional[`discord.Client`]
   >    - The Bot Instance to Use for Fetching
   > - military_time: Optional[`bool`]
   >    - Whether to Use Military Time
   > - before: Optional[`datetime.datetime`]
   >    - The Time to Capture Messages Before
   > - after: Optional[`datetime.datetime`]
   >    - The Time to Capture Messages After
   > - attachment_handler: Optional[`AttachmentHandler`]
   >    - The Attachment Handler to Use
   >
   >
   > #### Returns:
   > - Optional[`str`]
   >    - The HTML of the Export
   >
   > #### Example:
   > ```python
   > import discord
   > from discord.ext import commands
   >
   > import chat_exporter
   > import io
   >
   > bot = commands.Bot(...)
   >
   > @bot.command()
   > @commands.guild_only()
   > async def export(ctx: commands.Context):
   >    transcript = await chat_exporter.export(
   >        ctx.channel,
   >        bot=bot,
   >        military_time=False,
   >    )
   >    if transcript is None: # Failed to Create Transcript - Traceback is Printed to Console
   >        return
   >
   >   await ctx.reply(
   >       file=discord.File(
   >           io.StringIO(transcript),
   >           filename="transcript.html",
   >       )
   >   )
   > ```
</details>

<details>
   <summary><b>Advanced Usage via <code>.raw_export()</code></b></summary>

   > #### Parameters:
   > - channel: `discord.abc.Messageable`
   >    - The Channel to Export
   > - messages: `List[discord.Message]`
   >    - The Messages to Export
   > - bot: Optional[`discord.Client`]
   >    - The Bot Instance to Use for Fetching
   > - military_time: Optional[`bool`]
   >    - Whether to Use Military Time
   > - attachment_handler: Optional[`AttachmentHandler`]
   >    - The Attachment Handler to Use
   >
   >
   > #### Returns:
   > - Optional[`str`]
   >    - The HTML of the Export
   >
   > #### Example:
   > ```python
   > import discord
   > from discord.ext import commands
   >
   > import chat_exporter
   > import io
   >
   > bot = commands.Bot(...)
   >
   > @bot.command()
   > @commands.guild_only()
   > async def export(ctx: commands.Context):
   >    transcript = await chat_exporter.raw_export(
   >        ctx.channel,
   >        messages=[msg async for msg in ctx.channel.history(limit=None, oldest_first=True)],
   >        bot=bot,
   >    )
   >    if transcript is None: # Failed to Create Transcript - Traceback is Printed to Console
   >        return
   >
   >   await ctx.reply(
   >       file=discord.File(
   >           io.StringIO(transcript),
   >           filename="transcript.html",
   >       )
   >   )
   > ```
</details>

<br />

### Handling Attachments:
As Discord has Restricted their CDN so that Attachment Proxy-URLs are Temporary (hence the 'Broken'/Invalid Attachments in Transcripts), You have to Provide an `AttachmentHandler` to Resolve it.

If You Do Not Provide an `AttachmentHandler`, the Library will Use the Default (Temporary) Proxy-URLs.

<details>
   <summary><b>Creating your Own <code>AttachmentHandler</code> (Recommended)</b></summary>

   > All Custom `AttachmentHandler` Classes Must Inherit from `AttachmentHandler` & Implement the `process_asset` Method.
   >
   > #### Methods:
   > - `process_asset`:
   >    - Parameters:
   >       - attachment: `discord.Attachment`
   >          - The Attachment to Process
   >    - Returns:
   >       - `discord.Attachment`
   >          - The Attachment Object with Updated URLs
   >
   > #### Example:
   > ```python
   > class MyAttachmentHandler(chat_exporter.AttachmentHandler):
   >     def __init__(self, *args, **kwargs) -> None:
   >         ... # Your Initialisation Logic Here (If Any)
   >
   >     async def process_asset(self, attachment: discord.Attachment) -> discord.Attachment:
   >         new_url = ...  # Your Upload Logic Here
   >
   >         attachment.url = new_url
   >         attachment.proxy_url = new_url
   >         return attachment # Return the Attachment Object with Updated URLs
   >
   > attachment_handler = MyAttachmentHandler(...)
   >
   > ...
   >
   > # In your Code:
   > transcript = await chat_exporter.export(
   >     ...,
   >     attachment_handler=attachment_handler,
   > )
   > ```
</details>

<details>
   <summary><b>Storing Attachments Locally via <code>AttachmentToLocalFileHostHandler</code></b></summary>

   > This Class Stores the Attachments Locally on the File System & Provides a (Public) URL to Access it.
   >
   > #### Parameters:
   > - base_path: `str`
   >    - The Base Path to Store the Attachments
   > - url_base: `str`
   >    - The Base URL to Access the Attachments
   >
   > #### Example:
   > ```python
   > attachment_handler = chat_exporter.AttachmentToLocalFileHostHandler(
   >     base_path="/usr/share/assets",
   >     url_base="https://your-domain.com/assets/",
   > )
   >
   > ...
   >
   > # In your Code:
   > transcript = await chat_exporter.export(
   >     ...,
   >     attachment_handler=attachment_handler,
   > )
   > ```
</details>

<details>
   <summary><b>Sending Attachments to a Discord Channel via <code>AttachmentToDiscordChannel</code> (NOT Recommended)</b></summary>

   > This Handler Sends the Attachments to a Discord Channel & Provides the New (but Still Temporary) Proxy-URLs to Access it.
   >
   > #### Parameters:
   > - channel: `discord.ab.Messageable`
   >    - The Channel to Store the Attachments
   >
   > #### Example:
   > ```python
   > attachment_handler = chat_exporter.AttachmentToDiscordChannel(
   >     channel=bot.get_channel(...),
   > )
   >
   > ...
   >
   > # In your Code:
   > transcript = await chat_exporter.export(
   >     ...,
   >     attachment_handler=attachment_handler,
   > )
   > ```
</details>

<br />

### Other Functions:

<details>
   <summary><b>Generating an Embed to Link the Transcript via <code>.quick_link()</code></b></summary>

   > #### Parameters:
   > - channel: `discord.abc.Messageable`
   >    - The Channel to Send the Link
   > - message: `discord.Message`
   >    - The Message to Get the Transcript From
   >
   > #### Returns:
   > - `discord.Message`
   >    - The Message of the Link
   >
   > #### Example:
   > ```python
   > @bot.command()
   > @commands.guild_only()
   > async def export(ctx: commands.Context):
   >    output = await chat_exporter.quick_export(...)
   >    if output is None: # Failed to Create Transcript - Traceback is Printed to Console
   >        return
   >
   >    await chat_exporter.quick_link(ctx.channel, output)
   > ```
</details>

<details>
   <summary><b>Generating a Link to View the Transcript via <code>.link()</code></b></summary>

   > #### Parameters:
   > - message: `discord.Message`
   >    - The Message to Get the Transcript From
   >
   > #### Returns:
   > - `str`
   >    - The URL of the Transcript
   >
   > #### Example:
   > ```python
   > @bot.command()
   > @commands.guild_only()
   > async def export(ctx: commands.Context):
   >    output = await chat_exporter.quick_export(...)
   >    if output is None: # Failed to Create Transcript - Traceback is Printed to Console
   >        return
   >
   >    url = chat_exporter.link(output)
   >    await ctx.reply(f"[View Transcript]({url})")
   > ```
</details>

<br />

## Contributing

### Issues & Feature Requests:
If You Found a Bug or Have a Feature Request, Please Open an [Issue](https://github.com/1337Syntax/DiscordChatExporterPy/issues 'Issues').

### Pull Requests:
If You Want to Contribute to the Project, Please Fork the Repository & Install the Development Requirements from `requirements/dev.txt`. Then when Ready, Open a [Pull Request](https://github.com/1337Syntax/DiscordChatExporterPy/pulls 'Pull Requests')!

<br />

## Attributions
This Package was Imported from the Original [DiscordChatExporterPy](https://github.com/mahtoid/DiscordChatExporterPy 'mahtoid/DiscordChatExporterPy').

<br />

## License
This Project is Licensed Under the [GNU General Public License v3.0](/LICENSE 'License').
