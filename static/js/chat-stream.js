/*
   Chat Stream Handler JavaScript
   
   Handles real-time streaming of AI responses using Fetch API.
   
   TODO: Day 4 Implementation
   - Connect to POST /chat endpoint
   - Handle streaming response chunks
   - Append to chat display in real-time
   - Handle errors
   - Format response with markdown (optional)
*/

/**
 * Stream chat response from server.
 * 
 * TODO: Day 4 - Implement full streaming logic
 * 
 * Steps:
 * 1. Send POST request to /chat with query and document_id
 * 2. Use fetch(...).body.getReader() for streaming
 * 3. Read chunks and decode from Uint8Array
 * 4. Append each chunk to chat display
 * 5. Auto-scroll to latest message
 * 6. Handle end of stream and error cases
 */
async function streamChatResponse(query, documentId) {
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
        
        // TODO: Day 4 - Handle streaming response
        // const reader = response.body.getReader();
        // const decoder = new TextDecoder();
        // while (true) {
        //     const { done, value } = await reader.read();
        //     if (done) break;
        //     const chunk = decoder.decode(value);
        //     // Append chunk to chat display
        // }
        
        console.log('Stream response received (TODO: implement)');
    } catch (error) {
        console.error('Error streaming response:', error);
    }
}

/**
 * Append message to chat history display.
 * 
 * TODO: Create message HTML element and add to chat-history div
 */
function appendMessageToChat(message, isUserMessage = false) {
    // TODO: Day 4 - Implement message appending
    console.log('Appending message:', message);
}

/**
 * Create message HTML element.
 * 
 * TODO: Format message with proper styling and timestamps
 */
function createMessageElement(content, isUserMessage = false, timestamp = null) {
    // TODO: Day 4 - Implement message element creation
    const messageDiv = document.createElement('div');
    // ... implement
    return messageDiv;
}
