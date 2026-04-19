"""Gradio application for the Music Store Multi-Agent System."""

import uuid
import time
import logging

import gradio as gr
from langchain_core.messages import HumanMessage, AIMessage

from src.config import settings
from src.db.database import verify_database
from src.agents.graph import build_graph
from src.ui.styles import CUSTOM_CSS

logger = logging.getLogger(__name__)

# Module-level state
_graph = None
_checkpointer = None
_store = None


def initialize():
    global _graph, _checkpointer, _store

    logger.info("Initializing Music Store Agent...")

    db_health = verify_database()
    if db_health.get("status") != "healthy":
        logger.error(f"Database unhealthy: {db_health}")
    else:
        logger.info(f"Database healthy: {db_health['tables']}")

    try:
        _graph, _checkpointer, _store = build_graph(
            model_name=settings.model_name,
            temperature=settings.temperature,
        )   
        logger.info("Agent graph built successfully.")
    except Exception as e:
        logger.error(f"Failed to build agent graph: {e}")
        raise


def _status_html(status: str, message: str, tools_used: list = None) -> str:
    colors = {
        "success": "#10b981",
        "error": "#ef4444",
        "warning": "#f59e0b",
        "waiting": "#6366f1",
        "idle": "#6b7280",
    }
    icons = {
        "success": "✓",
        "error": "✗",
        "warning": "⚠",
        "waiting": "⏳",
        "idle": "●",
    }
    color = colors.get(status, "#6b7280")
    icon = icons.get(status, "●")

    tools_text = ""
    if tools_used:
        tools_text = f" | Data sources: {', '.join(set(tools_used))}"

    return (
        f'<div style="display:flex;align-items:center;gap:6px;padding:6px 12px;'
        f'border-radius:6px;background:{color}15;border:1px solid {color}30;'
        f'font-size:13px;color:{color};">'
        f'<span>{icon}</span>'
        f'<span>{message}{tools_text}</span>'
        f'</div>'
    )


def reset_conversation() -> tuple:
    new_thread = str(uuid.uuid4())
    logger.info(f"Conversation reset. New thread_id={new_thread}")
    return [], new_thread, _status_html("idle", "New conversation started")


def show_user_message(message, history, tid):
    if not message.strip():
        return history, "", tid, _status_html("idle", "Ready")
    if not tid:
        tid = str(uuid.uuid4())
    history = history + [{"role": "user", "content": message}]
    return history, "", tid, _status_html("waiting", "Processing...")


def generate_response(history, tid):
    if not history:
        return history, tid, _status_html("idle", "Ready")

    user_message = None
    for msg in reversed(history):
        if msg.get("role") == "user":
            user_message = msg["content"]
            break

    if not user_message:
        return history, tid, _status_html("idle", "Ready")

    if not _graph:
        history.append({"role": "assistant", "content": "System not initialized. Please refresh the page."})
        return history, tid, _status_html("error", "System not initialized")

    config = {"configurable": {"thread_id": tid}}

    try:
        start_time = time.time()
        input_state = {"messages": [HumanMessage(content=user_message)]}

        final_response = None
        tools_used = []

        for event in _graph.stream(input_state, config=config, stream_mode="updates"):
            for node_name, node_output in event.items():
                logger.info(f"Graph event: node={node_name}")

                if node_name in ("music_tool_node",):
                    tools_used.append("music_catalog")
                elif node_name == "invoice_information_subagent":
                    tools_used.append("invoice_lookup")

                if isinstance(node_output, dict) and "messages" in node_output:
                    for msg in node_output["messages"]:
                        if isinstance(msg, AIMessage) and msg.content:
                            final_response = msg.content

        elapsed = time.time() - start_time

        if final_response:
            history.append({"role": "assistant", "content": final_response})
            status_out = _status_html(
                "success",
                f"Responded in {elapsed:.1f}s",
                tools_used=tools_used,
            )
        else:
            snapshot = _graph.get_state(config)
            if snapshot and hasattr(snapshot, "next") and snapshot.next:
                state_messages = snapshot.values.get("messages", [])
                for msg in reversed(state_messages):
                    if isinstance(msg, AIMessage) and msg.content:
                        final_response = msg.content
                        break

                if final_response and not any(
                    h.get("content") == final_response for h in history if h.get("role") == "assistant"
                ):
                    history.append({"role": "assistant", "content": final_response})

                status_out = _status_html("waiting", "Waiting for your input")
            else:
                history.append({
                    "role": "assistant",
                    "content": "I'm sorry, I wasn't able to generate a response. Please try rephrasing your question.",
                })
                status_out = _status_html("warning", "No response generated")

        return history, tid, status_out

    except Exception as e:
        logger.error(f"Error processing message: {e}", exc_info=True)
        history.append({"role": "assistant", "content": "I encountered an error. Please try again."})
        return history, tid, _status_html("error", str(e)[:100])


def create_app() -> gr.Blocks:
    initialize()

    with gr.Blocks(
        title=settings.app_title,
        css=CUSTOM_CSS,
        theme=gr.themes.Soft(
            primary_hue="blue",
            secondary_hue="slate",
            neutral_hue="slate",
            font=gr.themes.GoogleFont("Inter"),
        ),
    ) as app:

        thread_id = gr.State(value="")

        gr.HTML(
            f"""
            <div class="app-header">
                <h1>{settings.app_title}</h1>
                <p>{settings.app_description}</p>
            </div>
            """
        )

        chatbot = gr.Chatbot(
            value=[],
            height=480,
            show_label=False,
            avatar_images=(None, "https://api.dicebear.com/7.x/bottts/svg?seed=music"),
            elem_classes=["chatbot-container"],
            placeholder=(
                "**Welcome!** Type your message below to get started.\n\n"
                "Try: *\"My customer ID is 5\"* or *\"What rock albums do you have?\"*"
            ),
        )

        status = gr.HTML(
            value=_status_html("idle", "Ready — type a message to begin"),
            elem_classes=["status-bar"],
        )

        with gr.Row():
            msg_input = gr.Textbox(
                placeholder="Type your message here...",
                show_label=False,
                scale=6,
                container=False,
                autofocus=True,
            )
            send_btn = gr.Button("Send", variant="primary", scale=1, min_width=80)

        with gr.Row():
            reset_btn = gr.Button("New Conversation", size="sm", variant="secondary")

        gr.HTML(
            '<div class="app-footer">'
            'Powered by LangGraph Multi-Agent Architecture · '
            'Data from Chinook Sample Database'
            '</div>'
        )

        send_btn.click(
            fn=show_user_message,
            inputs=[msg_input, chatbot, thread_id],
            outputs=[chatbot, msg_input, thread_id, status],
        ).then(
            fn=generate_response,
            inputs=[chatbot, thread_id],
            outputs=[chatbot, thread_id, status],
        )

        msg_input.submit(
            fn=show_user_message,
            inputs=[msg_input, chatbot, thread_id],
            outputs=[chatbot, msg_input, thread_id, status],
        ).then(
            fn=generate_response,
            inputs=[chatbot, thread_id],
            outputs=[chatbot, thread_id, status],
        )

        reset_btn.click(
            fn=reset_conversation,
            inputs=[],
            outputs=[chatbot, thread_id, status],
        )

    return app
