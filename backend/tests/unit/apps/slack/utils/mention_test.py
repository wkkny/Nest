import pytest

from apps.slack.utils.mention import get_query


def rich_text(*elements):
    return [{"type": "rich_text", "elements": list(elements)}]


def section(*elements):
    return {"type": "rich_text_section", "elements": list(elements)}


def text(value):
    return {"type": "text", "text": value}


def user(user_id):
    return {"type": "user", "user_id": user_id}


class TestGetQuery:
    @pytest.mark.parametrize(
        ("blocks", "expected"),
        [
            (
                rich_text(
                    section(text("Hey "), user("U0BOT"), text(" what is the OWASP Top 10?"))
                ),
                "Hey what is the OWASP Top 10?",
            ),
            (
                rich_text(
                    section(
                        user("U0BOT"),
                        text(" is "),
                        {"type": "link", "url": "https://owasp.org/www-project-zap"},
                        text(" still an OWASP flagship project?"),
                    )
                ),
                "is https://owasp.org/www-project-zap still an OWASP flagship project?",
            ),
            (
                rich_text(
                    section(
                        user("U0BOT"),
                        text(" is "),
                        {
                            "type": "link",
                            "url": "https://owasp.org/www-project-zap",
                            "text": "owasp.org/www-project-zap",
                            "truncated": True,
                        },
                        text(" still a flagship project?"),
                    )
                ),
                "is https://owasp.org/www-project-zap still a flagship project?",
            ),
            (
                rich_text(
                    section(
                        user("U0BOT"),
                        text(" see "),
                        {"type": "link", "url": "https://owasp.org/", "text": "owasp.org"},
                    )
                ),
                "see https://owasp.org/",
            ),
            (
                rich_text(
                    section(
                        user("U0BOT"),
                        text(" what is "),
                        {"type": "link", "url": "https://www.zaproxy.org", "text": "ZAP"},
                        text("?"),
                    )
                ),
                "what is ZAP (https://www.zaproxy.org)?",
            ),
            (
                rich_text(
                    section(
                        user("U0BOT"),
                        text(" "),
                        user("U0ALICE"),
                        text(" asked how to start an OWASP chapter?"),
                    )
                ),
                "asked how to start an OWASP chapter?",
            ),
            (
                rich_text(
                    section(user("U0BOT"), text(" compare these:")),
                    {
                        "type": "rich_text_list",
                        "style": "bullet",
                        "elements": [section(text("ZAP")), section(text("Juice Shop"))],
                    },
                ),
                "compare these: ZAP Juice Shop",
            ),
            (
                rich_text(
                    section(user("U0BOT"), text(" what does this mean?")),
                    {"type": "rich_text_quote", "elements": [text("Broken access control")]},
                    {"type": "rich_text_preformatted", "elements": [text("eval(input)")]},
                ),
                "what does this mean? Broken access control eval(input)",
            ),
            (
                rich_text(
                    section(
                        user("U0BOT"),
                        {"type": "emoji", "name": "wave"},
                        text(" what is SAMM in "),
                        {"type": "channel", "channel_id": "C0GENERAL"},
                        {"type": "broadcast", "range": "here"},
                        text("?"),
                    )
                ),
                "what is SAMM in ?",
            ),
            (
                rich_text(section(user("U0BOT"), text("  what   is\nSAMM?  "))),
                "what is SAMM?",
            ),
        ],
    )
    def test_get_query_from_blocks(self, blocks, expected):
        """Test the query includes every text fragment and link without user mentions."""
        assert get_query({"text": "ignored", "blocks": blocks}) == expected

    @pytest.mark.parametrize(
        ("event", "expected"),
        [
            ({"text": "<@U0BOT> what is OWASP?"}, "what is OWASP?"),
            ({"text": "<@U0BOT> ask <@W0ALICE|alice> about ZAP"}, "ask about ZAP"),
            (
                {"text": "Fallback text", "blocks": rich_text(section(user("U0BOT")))},
                "Fallback text",
            ),
            ({"text": "Fallback text", "blocks": [{"type": "section"}]}, "Fallback text"),
        ],
    )
    def test_get_query_falls_back_to_text(self, event, expected):
        """Test the event text is used without user mentions when blocks have no text."""
        assert get_query(event) == expected

    @pytest.mark.parametrize(
        "event",
        [
            {},
            {"text": ""},
            {"text": "<@U0BOT>", "blocks": rich_text(section(user("U0BOT")))},
            {"text": "<@U0BOT> ", "blocks": rich_text(section(user("U0BOT"), text(" ")))},
        ],
    )
    def test_get_query_empty(self, event):
        """Test a mention without a question produces an empty query."""
        assert get_query(event) == ""
