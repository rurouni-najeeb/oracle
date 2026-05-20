import nh3
from markupsafe import Markup
from markdown_it import MarkdownIt
from fastapi.templating import Jinja2Templates

md = MarkdownIt("zero").enable(["link", "emphasis", "backticks", "strikethrough"])

_ALLOWED_TAGS = {"a", "strong", "em", "code", "s", "del"}
_ALLOWED_ATTRIBUTES = {"a": {"href", "title"}}
_ALLOWED_URL_SCHEMES = {"http", "https", "mailto"}


def render_inline_md(text: str) -> Markup:
    raw_html = md.renderInline(text)
    safe_html = nh3.clean(
        raw_html,
        tags=_ALLOWED_TAGS,
        attributes=_ALLOWED_ATTRIBUTES,
        url_schemes=_ALLOWED_URL_SCHEMES,
    )
    return Markup(safe_html)


def init_templates() -> Jinja2Templates:
    t = Jinja2Templates(directory="app/templates")
    t.env.filters["md"] = render_inline_md
    return t


templates = init_templates()
