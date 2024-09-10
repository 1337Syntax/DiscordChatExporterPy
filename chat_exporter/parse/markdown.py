import base64
import html
import random
import re
import string

from typing import Dict, List, Optional

from ..ext import convert_emoji


class ParseMarkdown:
    """The Markdown Parser"""

    CODE_BLOCK_CONTENT: Dict[str, str] = {}

    def __init__(self, content: str) -> None:
        self.__content = content

    @property
    def content(self) -> str:
        return self.__content

    @content.setter
    def content(self, value: str) -> None:
        self.__content = value

    async def standard_message_flow(self) -> str:
        self.parse_code_block_markdown()
        self.https_http_links()
        self.parse_embedded_links()
        self.parse_normal_markdown()

        await self.parse_emoji()
        return self.content

    async def standard_embed_flow(self) -> str:
        self.parse_code_block_markdown()
        self.https_http_links()
        self.parse_embedded_links()
        self.parse_embed_markdown()
        self.parse_normal_markdown()

        await self.parse_emoji()
        return self.content

    async def special_embed_flow(self) -> str:
        self.parse_code_block_markdown()
        self.https_http_links()
        self.parse_embedded_links()
        self.parse_normal_markdown()

        await self.parse_emoji()
        return self.content

    async def message_reference_flow(self) -> str:
        self.strip_preserve()
        self.parse_code_block_markdown(reference=True)
        self.https_http_links()
        self.parse_embedded_links()
        self.parse_normal_markdown()
        self.parse_br()

        return self.content

    async def special_emoji_flow(self) -> str:
        await self.parse_emoji()
        return self.content

    def parse_br(self) -> None:
        self.__content = self.__content.replace("<br>", " ")

    async def parse_emoji(self) -> None:
        holder = (
            [
                r"&lt;:.*?:(\d*)&gt;",
                '<img class="emoji emoji--small" src="https://cdn.discordapp.com/emojis/%s.png">',
            ],
            [
                r"&lt;a:.*?:(\d*)&gt;",
                '<img class="emoji emoji--small" src="https://cdn.discordapp.com/emojis/%s.gif">',
            ],
            [
                r"<:.*?:(\d*)>",
                '<img class="emoji emoji--small" src="https://cdn.discordapp.com/emojis/%s.png">',
            ],
            [
                r"<a:.*?:(\d*)>",
                '<img class="emoji emoji--small" src="https://cdn.discordapp.com/emojis/%s.gif">',
            ],
        )

        self.__content = await convert_emoji(self.__content)

        for x in holder:
            p, r = x
            match = re.search(p, self.__content)
            while match is not None:
                emoji_id = match.group(1)
                self.__content = self.__content.replace(
                    self.__content[match.start():match.end()],
                    r % emoji_id,
                )
                match = re.search(p, self.__content)

    def strip_preserve(self) -> None:
        p = r'<span class="chatlog__markdown-preserve">(.*)</span>'
        r = '%s'

        pattern = re.compile(p)
        match = re.search(pattern, self.__content)
        while match is not None:
            affected_text = match.group(1)
            self.__content = self.__content.replace(
                self.__content[match.start():match.end()],
                r % affected_text,
            )
            match = re.search(pattern, self.__content)

    def ordered_list_markdown_to_html(self) -> None:
        lines = self.__content.split('\n')
        html = ''
        indent_stack = [0]
        started = True

        for line in lines:
            match = re.match(r'^(\s*)(\d+\.)\s+(.+)$', line)
            if match:
                indent, bullet, content = match.groups()
                indent = len(indent)

                if started:
                    html += '<ol class="markup" style="padding-left: 20px;margin: 0 !important">\n'
                    started = False
                if indent % 2 == 0:
                    while indent < indent_stack[-1]:
                        html += '</ol>\n'
                        indent_stack.pop()
                    if indent > indent_stack[-1]:
                        html += '<ol class="markup">\n'
                        indent_stack.append(indent)
                else:
                    while indent + 1 < indent_stack[-1]:
                        html += '</ol>\n'
                        indent_stack.pop()
                    if indent + 1 > indent_stack[-1]:
                        html += '<ol class="markup">\n'
                        indent_stack.append(indent + 1)

                html += f'<li class="markup">{content.strip()}</li>\n'
            else:
                while len(indent_stack) > 1:
                    html += '</ol>'
                    indent_stack.pop()
                if not started:
                    html += '</ol>'
                    started = True
                html += line + '\n'

        while len(indent_stack) > 1:
            html += '</ol>\n'
            indent_stack.pop()

        self.__content: str = html

    def unordered_list_markdown_to_html(self) -> None:
        lines = self.__content.split('\n')
        html = ''
        indent_stack = [0]
        started = True

        for line in lines:
            match = re.match(r'^(\s*)([-*])\s+(.+)$', line)
            if match:
                indent, bullet, content = match.groups()
                indent = len(indent)

                if started:
                    html += '<ul class="markup" style="padding-left: 20px;margin: 0 !important">\n'
                    started = False
                if indent % 2 == 0:
                    while indent < indent_stack[-1]:
                        html += '</ul>\n'
                        indent_stack.pop()
                    if indent > indent_stack[-1]:
                        html += '<ul class="markup">\n'
                        indent_stack.append(indent)
                else:
                    while indent + 1 < indent_stack[-1]:
                        html += '</ul>\n'
                        indent_stack.pop()
                    if indent + 1 > indent_stack[-1]:
                        html += '<ul class="markup">\n'
                        indent_stack.append(indent + 1)

                html += f'<li class="markup">{content.strip()}</li>\n'
            else:
                while len(indent_stack) > 1:
                    html += '</ul>'
                    indent_stack.pop()
                if not started:
                    html += '</ul>'
                    started = True
                html += line + '\n'

        while len(indent_stack) > 1:
            html += '</ul>\n'
            indent_stack.pop()

        self.__content: str = html

    def parse_normal_markdown(self) -> None:
        self.ordered_list_markdown_to_html()
        self.unordered_list_markdown_to_html()

        holder = (
            [r"(?<!\\)__(.*?)__", r'<span style="text-decoration: underline">\1</span>'],
            [r"(?<!\\)\*\*(.*?)\*\*", r'<strong>\1</strong>'],
            [r"(?<!\\)\*(.*?)\*", r'<em>\1</em>'],
            [r"(?<!\\)_([^_]+)_", r'<em>\1</em>'],
            [r"(?<!\\)~~(.*?)~~", r'<span style="text-decoration: line-through">\1</span>'],
            [r"(^|\n)###\s(.*?)\n", r'\1<h3>\2</h3>\n'],
            [r"(^|\n)##\s(.*?)\n", r'\1<h2>\2</h2>\n'],
            [r"(^|\n)#\s(.*?)\n", r'\1<h1>\2</h1>\n'],
            [r"(?<!\\)\|\|(.*?)\|\|", r'<span class="spoiler spoiler--hidden" onclick="showSpoiler(event, this)"> <span class="spoiler-text">\1</span></span>'],
        )
        for pattern, replacement in holder:
            self.__content = re.sub(pattern, replacement, self.__content)

        # > quote
        content = re.sub(r"\n", "<br>", self.__content).split("<br>")
        pattern = re.compile(r"^&gt;\s*(.+)")

        if len(content) == 1:
            if re.search(pattern, content[0]):
                self.content = f'<div class="quote">{content[0][5:]}</div>'
                return
            self.content = content[0]
            return

        y = None
        new_content = ""
        for x in content:
            if re.search(pattern, x) and y:
                y = y + "<br>" + x[5:]
            elif not y:
                if re.search(pattern, x):
                    y = x[5:]
                else:
                    new_content = new_content + x + "<br>"
            else:
                new_content = new_content + f'<div class="quote">{y}</div>'
                new_content = new_content + x
                y = ""

        if y:
            new_content = new_content + f'<div class="quote">{y}</div>'

        self.content = re.sub("<br>", "\n", new_content)

    def parse_code_block_markdown(self, reference: bool = False) -> None:
        def _create_unique_id() -> str:
            _id = "{{CODEBLOCK" + base64.b64encode(
                ''.join(
                    random.choices(
                        string.ascii_letters +
                        string.digits, k=16,
                    ),
                ).encode(),
            ).decode() + "}}"
            if _id in ParseMarkdown.CODE_BLOCK_CONTENT or _id in self.__content:
                return _create_unique_id()
            else:
                return _id

        markdown_languages = [
            "asciidoc", "autohotkey", "bash",
            "coffeescript", "cpp", "cs", "css",
            "diff", "fix", "glsl", "ini", "json",
            "md", "ml", "prolog", "py", "tex",
            "xl", "xml", "js", "html",
        ]
        self.__content = re.sub(r"\n", "<br>", self.__content)

        # ```code```
        pattern = re.compile(r"```(.*?)```")
        match = re.search(pattern, self.__content)
        while match is not None:
            language_class = "nohighlight"
            affected_text = match.group(1)

            for language in markdown_languages:
                if affected_text.lower().startswith(language):
                    language_class = f"language-{language}"
                    _, _, affected_text = affected_text.partition('<br>')

            affected_text = self.return_to_markdown(affected_text)

            second_pattern = re.compile(r"^<br>|<br>$")
            second_match = re.search(second_pattern, affected_text)
            while second_match is not None:
                affected_text = re.sub(r"^<br>|<br>$", '', affected_text)
                second_match = re.search(second_pattern, affected_text)

            affected_text = re.sub("  ", "&nbsp;&nbsp;", affected_text)

            _id = _create_unique_id()
            ParseMarkdown.CODE_BLOCK_CONTENT[_id] = affected_text

            if not reference:
                self.__content = self.__content.replace(
                    self.__content[match.start():match.end()],
                    '<div class="pre pre--multiline %s">%s</div>' % (
                        language_class, _id,
                    ),
                )
            else:
                self.__content = self.__content.replace(
                    self.__content[match.start():match.end()],
                    '<span class="pre pre-inline">%s</span>' % _id,
                )

            match = re.search(pattern, self.__content)

        # ``code``
        pattern = re.compile(r"``(.*?)``")
        match = re.search(pattern, self.__content)
        while match is not None:
            affected_text = match.group(1)
            affected_text = self.return_to_markdown(affected_text)
            _id = _create_unique_id()
            ParseMarkdown.CODE_BLOCK_CONTENT[_id] = affected_text
            self.__content = self.__content.replace(
                self.__content[match.start():match.end()],
                '<span class="pre pre-inline">%s</span>' % _id,
            )
            match = re.search(pattern, self.__content)

        # `code`
        pattern = re.compile(r"`(.*?)`")
        match = re.search(pattern, self.__content)
        while match is not None:
            affected_text = match.group(1)
            affected_text = self.return_to_markdown(affected_text)
            _id = _create_unique_id()
            ParseMarkdown.CODE_BLOCK_CONTENT[_id] = affected_text
            self.__content = self.__content.replace(
                self.__content[match.start():match.end()],
                '<span class="pre pre-inline">%s</span>' % _id,
            )
            match = re.search(pattern, self.__content)

        self.__content = re.sub(r"<br>", "\n", self.__content)

    @staticmethod
    def reverse_code_block_markdown(content: str) -> str:
        for key, value in ParseMarkdown.CODE_BLOCK_CONTENT.items():
            content = content.replace(key, value)

        return re.sub(r"<br>", "\n", content)

    def parse_embedded_links(self) -> None:
        # [Text](Link 'Title')

        pattern = re.compile(
            r"\[([^\]]+)\]\(([^)]+?)(?:\s*&#x27;([^&#]+)&#x27;)?\)",
            re.DOTALL,
        )
        matches = pattern.finditer(self.__content)

        modified_parts: List[str] = []
        last_end = 0

        for match in matches:
            affected_text = match.group(1)
            affected_url = match.group(2)
            affected_title = match.group(3)

            if not affected_text or not affected_url:
                continue

            affected_text = html.unescape(affected_text)
            affected_url = html.unescape(affected_url)
            affected_title = html.unescape(affected_title) if affected_title else None

            if affected_url[0] == "<" and affected_url[-1] == ">":
                affected_url = affected_url[1:-1]

            if affected_url.startswith("http://") or affected_url.startswith("https://"):
                affected_url = affected_url
            else:
                affected_url = None

            if affected_url and affected_title:
                replacement = f'<a href="{affected_url}" target="_blank" title="{affected_title}">{affected_text}</a>'
            elif affected_url:
                replacement = f'<a href="{affected_url}" target="_blank">{affected_text}</a>'
            else:
                continue

            modified_parts.append(self.__content[last_end:match.start()])
            modified_parts.append(replacement)
            last_end = match.end()

        modified_parts.append(self.__content[last_end:])

        self.__content = ''.join(modified_parts)

    def parse_embed_markdown(self) -> None:
        content = self.__content.split("\n")
        y = None
        new_content = ""
        pattern = re.compile(r"^>\s(.+)")

        if len(content) == 1:
            if re.search(pattern, content[0]):
                self.__content = f'<div class="quote">{content[0][2:]}</div>'
                return
            self.__content = content[0]
            return

        for x in content:
            if re.search(pattern, x) and y:
                y = y + "\n" + x[2:]
            elif not y:
                if re.search(pattern, x):
                    y = x[2:]
                else:
                    new_content = new_content + x + "\n"
            else:
                new_content = new_content + f'<div class="quote">{y}</div>'
                new_content = new_content + x
                y = ""

        if y:
            new_content = new_content + f'<div class="quote">{y}</div>'

        self.__content = new_content

    def return_to_markdown(self, content: str) -> str:
        holders = (
            [r"<strong>(.*?)</strong>", '**%s**'],
            [r"<em>([^<>]+)</em>", '*%s*'],
            [r"<h1>([^<>]+)</h1>", '# %s'],
            [r"<h2>([^<>]+)</h2>", '## %s'],
            [r"<h3>([^<>]+)</h3>", '### %s'],
            [r'<span style="text-decoration: underline">([^<>]+)</span>', '__%s__'],
            [r'<span style="text-decoration: line-through">([^<>]+)</span>', '~~%s~~'],
            [r'<div class="quote">(.*?)</div>', '> %s'],
            [r'<span class="spoiler spoiler--hidden" onclick="showSpoiler\(event, this\)"> <span class="spoiler-text">(.*?)<\/span><\/span>', '||%s||'],
            [r'<span class="unix-timestamp" data-timestamp=".*?" data-timestamp-format=".*?" data-timestamp-raw="(.*?)">', '%s'],
            [
                r'<a href="([^"]+)" target="_blank" title="([^"]+)">([^<]+)</a>',
                '[%s](%s "%s")',
            ],
            [r'<a href="([^"]+)" target="_blank">([^<]+)</a>', '[%s](%s)'],
            [r'<a href="([^"]+)" target="_blank">([^<]+)</a>', '%s'],
        )

        for x in holders:
            p, r = x
            pattern = re.compile(p)
            match = re.search(pattern, content)
            while match is not None:
                affected_text = match.group(1)
                content = content.replace(
                    content[match.start():match.end()],
                    r % html.escape(affected_text),
                )
                match = re.search(pattern, content)

        return content.lstrip().rstrip()

    def https_http_links(self) -> None:
        def remove_silent_link(url: str, raw_url: Optional[str] = None) -> str:
            pattern = rf"`.*{raw_url}.*`"
            match = re.search(pattern, self.__content)

            if "&lt;" in url and "&gt;" in url and not match:
                return url.replace("&lt;", "").replace("&gt;", "")
            return url

        content = re.sub("\n", "<br>", self.__content)
        output: List[str] = []

        if "http://" in content or "https://" in content and "](" not in content:
            for word in content.replace("<br>", " <br>").split():
                if "http" not in word:
                    output.append(word)
                    continue

                if "&lt;" in word and "&gt;" in word:
                    pattern = r"&lt;https?:\/\/(.*)&gt;"
                    match_url = re.search(pattern, word)
                    if match_url:
                        match_url = match_url.group(1)
                        url = f'<a href="https://{match_url}" target="_blank">https://{match_url}</a>'
                        word = word.replace("https://" + match_url, url)
                        word = word.replace("http://" + match_url, url)
                    output.append(remove_silent_link(word, match_url))

                elif "https://" in word:
                    pattern = r"https://[^\s>`\"*]*"
                    word_link = re.search(pattern, word)
                    if word_link and word_link.group().endswith(")"):
                        output.append(word)
                        continue
                    elif word_link:
                        word_link = word_link.group()
                        word_full = f'<a href="{word_link}" target="_blank">{word_link}</a>'
                        word = re.sub(pattern, word_full, word)
                    output.append(remove_silent_link(word))

                elif "http://" in word:
                    pattern = r"http://[^\s>`\"*]*"
                    word_link = re.search(pattern, word)
                    if word_link and word_link.group().endswith(")"):
                        output.append(word)
                        continue
                    elif word_link:
                        word_link = word_link.group()
                        word_full = f'<a href="{word_link}" target="_blank">{word_link}</a>'
                        word = re.sub(pattern, word_full, word)
                    output.append(remove_silent_link(word))

                else:
                    output.append(word)

            content = " ".join(output)
            self.__content = re.sub("<br>", "\n", content)
