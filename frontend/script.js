document.getElementById('start-button').addEventListener('click', startTest);

let userId = null;

function startTest() {
    fetch('http://localhost:8000/start_test', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        userId = data.user_id;
        getNextQuestion();
    });
}

function getNextQuestion() {
    fetch(`http://localhost:8000/next_question/${userId}`)
    .then(response => response.json())
    .then(data => {
        if (data.result) {
            showResult(data.result);
        } else {
            showQuestion(data);
        }
    });
}

function showQuestion(question) {
    document.getElementById('start-screen').style.display = 'none';
    document.getElementById('result-screen').style.display = 'none';
    document.getElementById('question-screen').style.display = 'block';

    document.getElementById('question-text').innerText = question.text;

    const answersDiv = document.getElementById('answers');
    answersDiv.innerHTML = '';
    question.answers.forEach(answer => {
        const button = document.createElement('button');
        button.classList.add('answer-button');
        button.innerText = answer.text;
        button.addEventListener('click', () => sendAnswer(question.question_id, answer.id));
        answersDiv.appendChild(button);
    });
}

function sendAnswer(questionId, answerId) {
    fetch('http://localhost:8000/answer', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            user_id: userId,
            question_id: questionId,
            answer_id: answerId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.result) {
            showResult(data.result);
        } else {
            showQuestion(data);
        }
    });
}

function showResult(result) {
    document.getElementById('start-screen').style.display = 'none';
    document.getElementById('question-screen').style.display = 'none';
    document.getElementById('result-screen').style.display = 'block';

    document.getElementById('result-text').innerText = result;
}
