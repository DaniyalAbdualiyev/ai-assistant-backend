# Simplified Web Chat Implementation Guide

This guide explains how to implement the simplified web chat flow that allows clients to chat with business assistants via a shared link without requiring authentication.

## Overview of the Simplified Chat Flow

1. **User accesses the shared link**: When a client clicks on the shared link, they are directed to a page that automatically initializes a chat session
2. **Client sends messages**: The client can immediately send messages without needing to provide any additional parameters
3. **Chat history is maintained**: The chat history is maintained through a client_id that is generated automatically and stored in the frontend

## Implementation

### 1. Initial Chat Page Load

When the client accesses the shared link, make a GET request to:

```
GET /web-chat/simplified/{business_unique_id}
```

This endpoint returns all necessary information:

```json
{
  "business_name": "Business Name",
  "business_type": "Type",
  "business_unique_id": "uuid-string",
  "client_id": "auto-generated-uuid",
  "session_key": "business-id_client-id",
  "welcome_message": "Welcome to Business Name! How can I assist you today?"
}
```

**Important**: Store the `client_id` in your frontend (localStorage, sessionStorage, etc.) to maintain the chat session.

### 2. Sending Messages

To send a message, use:

```
POST /web-chat/simplified-chat/{business_unique_id}
```

Request body:
```json
{
  "content": "User's message",
  "client_id": "the-client-id-from-step-1"
}
```

Response:
```json
{
  "content": "Assistant's response",
  "role": "assistant",
  "client_id": "client-id",
  "business_unique_id": "business-id",
  "business_name": "Business Name",
  "timestamp": "iso-timestamp"
}
```

### 3. Getting Chat History

To retrieve chat history:

```
GET /web-chat/simplified-history/{business_unique_id}?client_id={client_id}
```

Response:
```json
{
  "business_unique_id": "business-id",
  "client_id": "client-id",
  "messages": [
    {
      "role": "user",
      "content": "User message",
      "timestamp": "iso-timestamp"
    },
    {
      "role": "assistant",
      "content": "Assistant response",
      "timestamp": "iso-timestamp"
    }
  ]
}
```

## Example Implementation (JavaScript)

```javascript
// Initial page load
async function initChat(businessUniqueId) {
  const response = await fetch(`/web-chat/simplified/${businessUniqueId}`);
  const data = await response.json();
  
  // Store client_id for future requests
  localStorage.setItem('client_id', data.client_id);
  localStorage.setItem('business_unique_id', businessUniqueId);
  
  // Display welcome message
  displayMessage(data.welcome_message, 'assistant');
  
  return data;
}

// Send a message
async function sendMessage(message) {
  const businessUniqueId = localStorage.getItem('business_unique_id');
  const clientId = localStorage.getItem('client_id');
  
  // Display user message immediately
  displayMessage(message, 'user');
  
  const response = await fetch(`/web-chat/simplified-chat/${businessUniqueId}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      content: message,
      client_id: clientId
    })
  });
  
  const data = await response.json();
  
  // Display assistant response
  displayMessage(data.content, 'assistant');
}

// Load chat history
async function loadChatHistory() {
  const businessUniqueId = localStorage.getItem('business_unique_id');
  const clientId = localStorage.getItem('client_id');
  
  if (!businessUniqueId || !clientId) return;
  
  const response = await fetch(`/web-chat/simplified-history/${businessUniqueId}?client_id=${clientId}`);
  const data = await response.json();
  
  // Display messages
  data.messages.forEach(msg => {
    displayMessage(msg.content, msg.role);
  });
}

// Helper function to display messages
function displayMessage(content, role) {
  const chatContainer = document.getElementById('chat-container');
  const messageDiv = document.createElement('div');
  messageDiv.className = `message ${role}`;
  messageDiv.textContent = content;
  chatContainer.appendChild(messageDiv);
}
```

## Important Notes

1. The client_id is automatically generated when the client first accesses the chat page
2. There's no need for authentication or custom headers
3. All business-specific information is provided in the responses
4. Chat history is maintained as long as the client_id is preserved
5. If a client refreshes the page and the client_id is lost, a new session will start 