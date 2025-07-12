const socket = io();

const chatBox = document.getElementById('chat-box');
const chatForm = document.getElementById('chat-form');
const messageInput = document.getElementById('message');
let currentRoom = 'general';

function joinRoom() {
    const select = document.getElementById('room');
    const roomName = select.options[select.selectedIndex].text;
    const newRoom = select.value.trim();
    // console.log(currentRoom);
    // console.log(newRoom);
    if ((newRoom && newRoom !== currentRoom) && newRoom !== "None") {
        socket.emit('leave', { room: currentRoom });
        socket.emit('join', { room: newRoom });
        currentRoom = newRoom;
        chatBox.innerHTML= '';
        fetch(`/get_chats/${newRoom}`)
            .then(response => response.json())
            .then(data => {
                chatBox.innerHTML = '';
                chatBox.innerHTML = `<h1>${roomName}</h1>`;

                data.forEach(chat => {
                    const id = escapeHTML(chat.anonymous_userid || chat.user_id || "Anon");
                    const message = escapeHTML(chat.message || chat.msg || "");
                    const timestamp = escapeHTML(chat.timestamp || "Now");

                    const html = `<div class="chat-message">
                        <div class="chat-cont">
                        <span class="chat-id">${id}:</span>
                        <span class="chat-timestamp">${timestamp}</span>
                        </div>
                        <span class="chat-text">${message}</span>
                        </div>`;
                    chatBox.innerHTML += html;
                });
            });

        chatBox.scrollTop = chatBox.scrollHeight;
    }
}

chatForm.addEventListener('submit', function (e) {
    e.preventDefault();
    const msg = messageInput.value.trim();
    if (msg) {
        socket.emit('message', { room: currentRoom, msg });
        messageInput.value = '';
    }
});

function escapeHTML(str) {
    if (!str) return '';
    return str
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

socket.on('message', data => {
    // console.log(data);
    const messages = Array.isArray(data) ? data : [data];

    messages.forEach(chat => {
        const id = escapeHTML(chat.anonymous_userid || chat.user_id || "Anon");
        const message = escapeHTML(chat.message || chat.msg || "");
        const timestamp = escapeHTML(chat.timestamp || "Now");

        const html = `<div class="chat-message">
                        <div class="chat-cont">
                        <span class="chat-id">${id}:</span>
                        <span class="chat-timestamp">${timestamp}</span>
                        </div>
                        <span class="chat-text">${message}</span>
                        </div>`;
        chatBox.innerHTML += html;
    });

    chatBox.scrollTop = chatBox.scrollHeight;
});

socket.on('status', data => {
    chatBox.innerHTML += `<p><em>${data.msg}</em></p>`;
    chatBox.scrollTop = chatBox.scrollHeight;
});
