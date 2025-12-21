"""
Reviewer highlight feature - Cursor-style floating action bar
Shows a floating action bar when text is highlighted on flashcards
"""

from aqt import mw, gui_hooks


# JavaScript code to inject into the reviewer
HIGHLIGHT_BUBBLE_JS = """
(function() {
    // Only inject once
    if (window.ankiHighlightBubbleInjected) {
        return;
    }
    window.ankiHighlightBubbleInjected = true;
    console.log('Anki: Injecting highlight bubble for OpenEvidence');

    let bubble = null;
    let currentState = 'default'; // 'default' or 'input'
    let selectedText = '';
    let cmdKeyHeld = false;

    // Track Command/Meta key state
    document.addEventListener('keydown', (e) => {
        if (e.metaKey || e.key === 'Meta') {
            cmdKeyHeld = true;
        }
    });

    document.addEventListener('keyup', (e) => {
        if (!e.metaKey && e.key === 'Meta') {
            cmdKeyHeld = false;
        }
    });

    // Create the bubble element
    function createBubble() {
        const div = document.createElement('div');
        div.id = 'anki-highlight-bubble';
        div.style.cssText = `
            position: absolute;
            background: #1e1e1e;
            border-radius: 8px;
            border: 1px solid #4b5563;
            padding: 0px 5px;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3), 0 4px 6px -2px rgba(0, 0, 0, 0.2);
            z-index: 9999;
            display: none;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            font-size: 12px;
            color: #ffffff;
            line-height: 1;
            height: 24px;
        `;
        document.body.appendChild(div);
        return div;
    }

    // Render default state with two buttons and divider
    function renderDefaultState() {
        currentState = 'default';
        bubble.innerHTML = `
            <div style="display: flex; align-items: center; gap: 2px; height: 100%; line-height: 1;">
                <button id="add-to-chat-btn" style="
                    background: transparent;
                    border: none;
                    color: #ffffff;
                    padding: 0px 8px;
                    cursor: pointer;
                    border-radius: 4px;
                    font-size: 12px;
                    font-weight: 500;
                    transition: all 0.15s ease;
                    white-space: nowrap;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    height: 22px;
                    line-height: 22px;
                    display: inline-flex;
                    align-items: center;
                ">
                    Add to Chat
                </button>
                <div style="width: 1px; height: 16px; background-color: #4b5563;"></div>
                <button id="ask-question-btn" style="
                    background: transparent;
                    border: none;
                    color: #ffffff;
                    padding: 0px 8px;
                    cursor: pointer;
                    border-radius: 4px;
                    font-size: 12px;
                    font-weight: 500;
                    transition: all 0.15s ease;
                    white-space: nowrap;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    height: 22px;
                    line-height: 22px;
                    display: inline-flex;
                    align-items: center;
                ">
                    Ask Question
                </button>
            </div>
        `;

        // Add hover effects
        const addToChatBtn = bubble.querySelector('#add-to-chat-btn');
        const askQuestionBtn = bubble.querySelector('#ask-question-btn');

        addToChatBtn.addEventListener('mouseenter', () => {
            addToChatBtn.style.backgroundColor = '#374151';
        });
        addToChatBtn.addEventListener('mouseleave', () => {
            addToChatBtn.style.backgroundColor = 'transparent';
        });

        askQuestionBtn.addEventListener('mouseenter', () => {
            askQuestionBtn.style.backgroundColor = '#374151';
        });
        askQuestionBtn.addEventListener('mouseleave', () => {
            askQuestionBtn.style.backgroundColor = 'transparent';
        });

        // Add click handlers
        addToChatBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            handleAddToChat();
        });

        askQuestionBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            renderInputState();
        });
    }

    // Render input state with text field and submit button
    function renderInputState() {
        currentState = 'input';
        bubble.innerHTML = `
            <div style="display: flex; gap: 2px; align-items: center; height: 100%; line-height: 1;">
                <input
                    type="text"
                    id="question-input"
                    placeholder="Ask a question..."
                    style="
                        background: transparent;
                        border: none;
                        color: #ffffff;
                        padding: 0px 8px;
                        font-size: 12px;
                        font-weight: 500;
                        outline: none;
                        min-width: 200px;
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                        height: 22px;
                        line-height: 22px;
                    "
                />
                <button id="submit-btn" style="
                    background: #3b82f6;
                    border: none;
                    color: #ffffff;
                    padding: 0px 8px;
                    cursor: pointer;
                    border-radius: 9999px;
                    font-size: 14px;
                    font-weight: 600;
                    display: inline-flex;
                    align-items: center;
                    transition: all 0.15s ease;
                    height: 22px;
                    line-height: 22px;
                ">
                    →
                </button>
            </div>
        `;

        const input = bubble.querySelector('#question-input');
        const submitBtn = bubble.querySelector('#submit-btn');

        // Focus the input
        setTimeout(() => input.focus(), 0);

        // Submit on Enter key
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                handleSubmitQuestion();
            }
        });

        // Hover effect for submit button
        submitBtn.addEventListener('mouseenter', () => {
            submitBtn.style.backgroundColor = '#2563eb';
        });
        submitBtn.addEventListener('mouseleave', () => {
            submitBtn.style.backgroundColor = '#3b82f6';
        });

        // Click handler for submit button
        submitBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            handleSubmitQuestion();
        });
    }

    // Handle "Add to Chat" action
    function handleAddToChat() {
        console.log('Anki: Add to Chat clicked, text:', selectedText);
        // Send message to Python
        pycmd('openevidence:add_context:' + encodeURIComponent(selectedText));
        hideBubble();
    }

    // Handle question submission
    function handleSubmitQuestion() {
        const input = bubble.querySelector('#question-input');
        const query = input.value.trim();

        if (query) {
            console.log('Anki: Question submitted:', query, 'Context:', selectedText);
            // Send message to Python with format: query|context
            pycmd('openevidence:ask_query:' + encodeURIComponent(query) + '|' + encodeURIComponent(selectedText));
            hideBubble();
        }
    }

    // Position the bubble above the selection with 8px gap (doesn't overlap text)
    function positionBubble(rect) {
        const bubbleHeight = bubble.offsetHeight;
        const bubbleWidth = bubble.offsetWidth;
        const gap = 8; // Gap above selection to prevent covering text

        // Calculate center of selection
        const centerX = rect.left + (rect.width / 2);

        // Position bubble centered above selection with gap
        let left = centerX - (bubbleWidth / 2);
        let top = rect.top - bubbleHeight - gap;

        // Keep bubble within viewport bounds
        if (left < 0) left = 0;
        if (left + bubbleWidth > window.innerWidth) {
            left = window.innerWidth - bubbleWidth;
        }

        // If bubble would be above viewport, show it below instead
        if (top < 0) {
            top = rect.bottom + gap;
        }

        bubble.style.left = left + window.scrollX + 'px';
        bubble.style.top = top + window.scrollY + 'px';
    }

    // Show the bubble
    function showBubble(rect, text) {
        selectedText = text;
        renderDefaultState();
        bubble.style.display = 'block';

        // Position after render so we have accurate dimensions
        setTimeout(() => positionBubble(rect), 0);
    }

    // Hide the bubble
    function hideBubble() {
        bubble.style.display = 'none';
        currentState = 'default';
    }

    // Handle mouseup event
    document.addEventListener('mouseup', (e) => {
        // Small delay to allow selection to complete
        setTimeout(() => {
            const selection = window.getSelection();
            const text = selection.toString().trim();

            // Only show bubble if Command/Meta key is held AND text is selected
            if (text && text.length > 0 && cmdKeyHeld) {
                // Get selection range and position
                const range = selection.getRangeAt(0);
                const rect = range.getBoundingClientRect();

                showBubble(rect, text);
            } else {
                // No selection or no cmd key, hide bubble if clicking outside
                if (!bubble.contains(e.target)) {
                    hideBubble();
                }
            }
        }, 10);
    });

    // Hide bubble when clicking outside
    document.addEventListener('mousedown', (e) => {
        if (bubble && !bubble.contains(e.target)) {
            const selection = window.getSelection();
            if (!selection.toString().trim()) {
                hideBubble();
            }
        }
    });

    // Create the bubble on load
    bubble = createBubble();
    console.log('Anki: Highlight bubble ready');
})();
"""


def inject_highlight_bubble(html, card, context):
    """Inject the highlight bubble JavaScript into reviewer cards

    Args:
        html: The HTML of the question or answer
        card: The current card object
        context: One of "reviewQuestion", "reviewAnswer", "clayoutQuestion",
                "clayoutAnswer", "previewQuestion", "previewAnswer"

    Returns:
        Modified HTML with injected JavaScript
    """
    # Only inject in review context (not in card layout or preview)
    if context in ("reviewQuestion", "reviewAnswer"):
        # Add the JavaScript to the card HTML
        html += f"<script>{HIGHLIGHT_BUBBLE_JS}</script>"

    return html


def setup_highlight_hooks():
    """Register the highlight bubble injection hook"""
    gui_hooks.card_will_show.append(inject_highlight_bubble)
