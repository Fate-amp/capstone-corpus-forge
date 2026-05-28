/*
   Chat Stream Handler JavaScript
   
   Handles real-time streaming of AI responses using Fetch API.
*/

/**
 * Stream chat response from server.
 * 
 * Features:
 * - Sends POST request to /chat
 * - Streams chunks in real-time
 * - Updates UI progressively
 * - Handles errors gracefully
 */
async function streamChatResponse(query, documentId) {
    // Add user message immediately
    appendMessageToChat(query, true);

    // Create empty AI message container for streaming
    const aiMessageElement = appendMessageToChat('', false);

    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                query: query,
                document_id: documentId
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        // Ensure streaming is supported
        if (!response.body) {
            throw new Error('ReadableStream not supported in this browser.');
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        let fullResponse = '';

        while (true) {
            const { done, value } = await reader.read();

            // Stream finished
            if (done) {
                break;
            }

            // Decode chunk
            const chunk = decoder.decode(value, { stream: true });

            // Accumulate full response
            fullResponse += chunk;

            // Update AI message in real-time
            aiMessageElement.querySelector('.message-content').textContent =
                fullResponse;

            // Auto-scroll to bottom
            const chatHistory = document.getElementById('chat-history');
            chatHistory.scrollTop = chatHistory.scrollHeight;
        }

        console.log('Streaming completed successfully');

    } catch (error) {
        console.error('Error streaming response:', error);

        aiMessageElement.querySelector('.message-content').textContent =
            `Error: ${error.message}`;

        aiMessageElement.classList.add('error-message');
    }
}

/**
 * Append message to chat history display.
 * 
 * Returns the created message element so it can be updated during streaming.
 */
function appendMessageToChat(message, isUserMessage = false) {
    const chatHistory = document.getElementById('chat-history');

    // Create message element
    const messageElement = createMessageElement(message, isUserMessage);

    // Add to chat history
    chatHistory.appendChild(messageElement);

    // Auto-scroll
    chatHistory.scrollTop = chatHistory.scrollHeight;

    return messageElement;
}

/**
 * Create message HTML element.
 * 
 * Includes:
 * - Message styling
 * - Timestamp
 * - User/AI distinction
 */
function createMessageElement(
    content,
    isUserMessage = false,
    timestamp = null
) {
    const messageDiv = document.createElement('div');

    // Main message container class
    messageDiv.classList.add('chat-message');

    // Add role-specific class
    if (isUserMessage) {
        messageDiv.classList.add('user-message');
    } else {
        messageDiv.classList.add('ai-message');
    }

    // Create content element
    const contentDiv = document.createElement('div');
    contentDiv.classList.add('message-content');

    // Optional markdown rendering
    // If using marked.js:
    // contentDiv.innerHTML = marked.parse(content);

    // Plain text fallback
    contentDiv.textContent = content;

    // Create timestamp
    const timeDiv = document.createElement('div');
    timeDiv.classList.add('message-timestamp');

    const messageTime = timestamp || new Date();

    timeDiv.textContent = messageTime.toLocaleTimeString([], {
        hour: '2-digit',
        minute: '2-digit'
    });

    // Assemble message
    messageDiv.appendChild(contentDiv);
    messageDiv.appendChild(timeDiv);

    return messageDiv;
}