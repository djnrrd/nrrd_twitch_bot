function add_chat_msg(chat_msg) {
    document.getElementById("chat_overlay").
    insertAdjacentHTML("beforeend",
    `<div class="chat_message" id="${chat_msg.id}">
        <div class="display_name">
            <p class="display_name" style="color:${chat_msg.color}">
                ${chat_msg["display-name"]}:
            </p>
        </div>
        <div class="msg_text">
            <p class="msg_text">${chat_msg.msg_text}</p>
        </div>
    </div>
    `);
};

function delete_chat_messages(chat_msg) {
    if (chat_msg.username  == "") {
        document.getElementById("chat_overlay").innerHTML = "";
    };
};

function msg_handler(msg) {
    console.log(`[message] Data received from server: ${msg.data}`);
    const chat_msg = JSON.parse(msg.data);
    switch(chat_msg.msg_type) {
        case "privmsg":
            add_chat_msg(chat_msg);
            break;
        case "clearchat":
            delete_chat_messages(chat_msg);
            break;
    }
};

function connect() {
    var socket = new WebSocket("ws://localhost:8080/chat_overlay/ws/");

    socket.onopen = function(e) {
        console.log("[open] Connection established");
    };

    socket.onmessage = msg_handler;

    socket.onclose = function(event) {
        if (event.wasClean) {
            console.log(`[close] Connection closed cleanly, code=${event.code} reason=${event.reason}`);
        } else {
            // e.g. server process killed or network down
            // event.code is usually 1006 in this case
            // Sleep for 2 seconds and try again
            console.log('[close] Connection died');
            setTimeout(function() {connect();}, 2000);
        };
    };

    socket.onerror = function(error) {
        console.log(`[error] ${error.message}`);
    };
};

connect();
