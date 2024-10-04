document.addEventListener('DOMContentLoaded', function () {
    const chatBox = document.getElementById('chat-box');
    const chatInput = document.getElementById('chat-input');
    const sendBtn = document.getElementById('send-btn');
    let awaitingPatientID = false;
    let storedQuestion = '';

    function addMessage(content, sender) {
        const message = document.createElement('div');
        message.classList.add('message', sender);
        message.innerText = content;
        chatBox.appendChild(message);
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    function sendQuestion(question, patientID = null) {
        const body = patientID ? { question: storedQuestion, patient_id: patientID } : { question: question };
        fetch('/ask', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(body),
        })
        .then(response => response.json())
        .then(data => {
            if (data.response === 'Multiple patients found. Please provide the patient ID.') {
                awaitingPatientID = true;
                storedQuestion = question;
            }
            addMessage(data.response, 'bot');
        });
    }

    sendBtn.addEventListener('click', function () {
        const input = chatInput.value.trim();
        if (input) {
            addMessage(input, 'user');
            chatInput.value = '';
            if (awaitingPatientID) {
                sendQuestion(storedQuestion, input);
                awaitingPatientID = false;
                storedQuestion = '';
            } else {
                sendQuestion(input);
            }
        }
    });

    chatInput.addEventListener('keypress', function (e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            sendBtn.click();
        }
    });
});
