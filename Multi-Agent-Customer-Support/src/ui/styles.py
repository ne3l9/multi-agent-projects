"""CSS styles for the Gradio application."""

CUSTOM_CSS = """
.gradio-container {
    max-width: 900px !important;
    margin: 0 auto !important;
    font-family: 'Segoe UI', system-ui, -apple-system, sans-serif !important;
}
.app-header {
    text-align: center;
    padding: 24px 16px 16px;
    border-bottom: 1px solid #e5e7eb;
    margin-bottom: 16px;
}
.app-header h1 {
    font-size: 28px;
    font-weight: 700;
    color: #1f2937;
    margin: 0 0 8px;
}
.app-header p {
    font-size: 14px;
    color: #6b7280;
    margin: 0;
    line-height: 1.5;
}
.chatbot-container {
    border: 1px solid #e5e7eb !important;
    border-radius: 12px !important;
    overflow: hidden;
}
.status-bar {
    min-height: 36px;
}
.app-footer {
    text-align: center;
    padding: 12px;
    font-size: 12px;
    color: #9ca3af;
    border-top: 1px solid #f3f4f6;
    margin-top: 8px;
}
@media (max-width: 640px) {
    .app-header h1 { font-size: 22px; }
}
"""
