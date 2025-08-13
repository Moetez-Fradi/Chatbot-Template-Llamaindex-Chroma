const chatBox = document.getElementById('chat-box');
const chatForm = document.getElementById('chat-form');
const userInput = document.getElementById('user-input');

chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const message = userInput.value.trim();
    if (!message) return;
    
    appendMessage('user', message);
    userInput.value = '';
    
    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message })
        });
        const data = await response.json();
        appendMessage('bot', data.reply);
    } catch (err) {
        appendMessage('bot', 'Error: could not reach server.');
    }
});

function appendMessage(sender, text) {
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message', sender);
    
    // Create avatar
    const avatar = document.createElement('div');
    avatar.classList.add(sender === 'user' ? 'user-avatar' : 'bot-avatar');
    avatar.textContent = sender === 'user' ? 'U' : '🤖';
    
    // Create message content
    const messageContent = document.createElement('div');
    messageContent.classList.add('message-content');
    messageContent.textContent = text;
    
    // Append avatar and content to message
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(messageContent);
    
    // Add to chat box
    chatBox.appendChild(messageDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
}