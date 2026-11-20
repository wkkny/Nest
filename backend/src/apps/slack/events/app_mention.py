"""Slack app mention event handler."""

import logging

from apps.slack.blocks import markdown
from apps.slack.common.handlers.ai import get_blocks
from apps.slack.events.event import EventBase
from apps.slack.models import Conversation
from apps.slack.utils.mention import get_query

logger = logging.getLogger(__name__)

EMPTY_QUERY_MESSAGE = "👋 Hi! Ask me a question about OWASP, e.g. `@NestBot what is OWASP ZAP?`"


class AppMention(EventBase):
    """Handles app mention events when the bot is mentioned in a channel."""

    event_type = "app_mention"

    def handle_event(self, event, client):
        """Handle an incoming app mention event."""
        channel_id = event.get("channel")

        if not Conversation.objects.filter(
            is_nest_bot_assistant_enabled=True,
            slack_channel_id=channel_id,
        ).exists():
            logger.warning("NestBot AI Assistant is not enabled for this conversation.")
            return

        query = get_query(event)
        thread_ts = event.get("thread_ts") or event.get("ts")

        if not query:
            logger.warning("No query found in app mention")
            client.chat_postMessage(
                channel=channel_id,
                blocks=[markdown(EMPTY_QUERY_MESSAGE)],
                text=EMPTY_QUERY_MESSAGE,
                thread_ts=thread_ts,
            )
            return

        logger.info("Handling app mention")

        placeholder = client.chat_postMessage(
            channel=channel_id,
            blocks=[markdown("⏳ Thinking…")],
            text="Thinking…",
            thread_ts=thread_ts,
        )

        reply_blocks = get_blocks(query=query)
        client.chat_update(
            channel=channel_id,
            ts=placeholder["ts"],
            blocks=reply_blocks,
            text=query,
        )
