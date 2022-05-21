function add_chat_msg(chat_msg) {
    // Start with getting the overlay
    overlay = document.getElementById('chat_overlay');
    // Create the overall containing div
    msg_div = document.createElement('div');
    msg_div.id = chat_msg.id;
    msg_div.className = `chat_message ${chat_msg.id}`;
    // Add the Username and pronoun details
    name_div = document.createElement('div');
    name_div.className = 'display_name';
    name_p = document.createElement('p');
    name_p.className = 'display_name';
    name_p.style = `color:${chat_msg.color}`;
    name_text = document.createTextNode(`${chat_msg['display-name']}`);
    name_p.appendChild(name_text);
    name_div.appendChild(name_p);
    if (chat_msg.pronouns !== null) {
        pronoun_p = document.createElement('p');
        pronoun_p.className = 'pronoun_tag';
        pronoun_text = document.createTextNode(`(${chat_msg.pronouns})`);
        pronoun_p.appendChild(pronoun_text);
        name_div.appendChild(pronoun_p);
    }
    msg_div.appendChild(name_div);
    // Main message text
    text_div = document.createElement('div');
    text_div.className = 'msg_text';
    text_p = document.createElement('p');
    if (chat_msg.msg_text.includes('ACTION')) {
        text_p.className = 'msg_text slash_me';
        msg_text = chat_msg.msg_text.slice(7, -1);
        text_p.innerHTML = msg_text;
    }
    else {
        text_p.className = 'msg_text';
        text_p.innerHTML = `${chat_msg.msg_text}`;
    }
    text_div.appendChild(text_p);
    msg_div.appendChild(text_div);
    // Finally add the message to the overlay
    overlay.appendChild(msg_div);
}

function clear_out_of_bounds() {
    let chat_overlay = document.getElementById("chat_overlay");
    if (chat_overlay.getBoundingClientRect().y < 0) {
        console.log(chat_overlay.getBoundingClientRect().y);
        chat_messages = chat_overlay.getElementsByClassName("chat_message");
        chat_overlay.removeChild(chat_messages[0]);
    }
}

function delete_chat_messages(chat_msg) {
    if (chat_msg.username  == "") {
        document.getElementById("chat_overlay").innerHTML = "";
    } else {
        console.log(`Trying to remove messages for
                    ${chat_msg["target-user-id"]}`);
        const chats = document.getElementsByClassName
            (chat_msg["target-user-id"]);
        while (chats.length > 0) {
            chats[0].parentNode.removeChild(chats[0]);
        }
    }
}

function delete_individual_message(chat_msg) {
    document.getElementById(chat_msg["target-msg-id"]).innerHTML = "";
}

function msg_handler(msg) {
    console.log(`[message] Data received from server: ${msg.data}`);
    const chat_msg = JSON.parse(msg.data);
    switch(chat_msg.msg_type) {
        case "privmsg":
            add_chat_msg(chat_msg);
            clear_out_of_bounds();
            break;
        case "clearchat":
            delete_chat_messages(chat_msg);
            break;
        case "clearmsg":
            delete_individual_message(chat_msg);
            break;
    }
}

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
            console.log(`[close] Connection died code=${event.code} reason=${event.reason}`);
            setTimeout(function() {connect();}, 5000);
        };
    };

    socket.onerror = function(error) {
        console.log(`[error] ${error.message}`);
    };
}

connect();
