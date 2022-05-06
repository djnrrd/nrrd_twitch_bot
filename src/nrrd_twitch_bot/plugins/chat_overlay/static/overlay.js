
function add_chat_msg(msg) {
    console.log(`[message] Data received from server: ${event.data}`);
    const chat_msg = JSON.parse(event.data);
    document.getElementById('chat_overlay').
        insertAdjacentHTML("beforeend",
        `<div class="chat_message" id="${chat_msg.id}">
            <div class="display-name">
                <p style="color:${chat_msg.color}">
                    ${chat_msg["display-name"]}
                </p>
            </div>
            <div class="msg_text">
                <p>${chat_msg.msg_text}</p>
            </div>
        </div>
        `);
};


let socket = new WebSocket("ws://localhost:8080/chat_overlay/ws/");

socket.onopen = function(e) {
  console.log("[open] Connection established");
};

socket.onmessage = add_chat_msg;

socket.onclose = function(event) {
  if (event.wasClean) {
    console.log(`[close] Connection closed cleanly, code=${event.code} reason=${event.reason}`);
  } else {
    // e.g. server process killed or network down
    // event.code is usually 1006 in this case
    console.log('[close] Connection died');
  }
};

socket.onerror = function(error) {
  console.log(`[error] ${error.message}`);
};

function main() {
    const params = new URLSearchParams(document.location.hash);
    const keyVars = paramsToObject(params.entries());
    const StatusMessage = document.getElementById("status_message");
    const response = post_tokens(keyVars, StatusMessage);
    console.log(response);
}