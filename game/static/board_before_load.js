let newGameButton = document.querySelector('.new-game-button');
let currentPlayer;
let sign;


function getCookie(name){
  const cookieName = `${name}=`;
  const decodedCookie = decodeURIComponent(document.cookie);
  const cookieArray = decodedCookie.split(';');
  for (let i = 0; i < cookieArray.length; i++) {
    let cookie = cookieArray[i];
    while (cookie.charAt(0) === ' ') {
      cookie = cookie.substring(1);
    }
    if (cookie.indexOf(cookieName) === 0) {
      return cookie.substring(cookieName.length, cookie.length);
    }
  }
  return '';
}

function update_score(){
  fetch('http://localhost:8001/high_scores')
  .then(response => response.json())
  .then(data => {
    const scoresDiv = document.querySelector('.scores');

    // Clear the existing content
    scoresDiv.innerHTML = '';

    // Loop through the result list and create a <div> element for each item
    data.forEach((score, index) => {
      let new_score;
      if (score.score === null ) {
        new_score = 0
      } else {
        new_score = score.score
      }

      const mainContainer = document.createElement('div');
      mainContainer.classList.add('score-container');

      const time = document.createElement('div');
      time.textContent = `${index+1}: ${score.date}`;
      mainContainer.appendChild(time);

      const player = document.createElement('div');
      player.textContent = score.user;
      mainContainer.appendChild(player);

      const scoreElement = document.createElement('div');
      scoreElement.textContent = new_score;
      mainContainer.appendChild(scoreElement);

      const timePlayed = document.createElement('div');
      timePlayed.textContent = score.time_played;
      mainContainer.appendChild(timePlayed);

      scoresDiv.appendChild(mainContainer);

    });
  })
  .catch(error => {
    console.error('Error:', error);
  });
}

update_score()

const token = getCookie('access_token'); // Retrieve the JWT token from the cookie
const currentURL = window.location.href;
const match = currentURL.match(/\/session_view\/(\d+)\/game\/(\d+)/);
const sessionId = match[1];
const gameId = match[2];

console.log("Session ID:", sessionId);
console.log("Game ID:", gameId);

window.addEventListener('DOMContentLoaded', async () => {
  try {

    const url = `http://localhost:8001/session/${sessionId}/game/${gameId}`;

    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + token
      },
    });
    if (response.ok) {
      const data = await response.json();
      updateBoard(data);
      handleGameStatus(data.status, data.credits);
      update_score()
      currentPlayer = data["player_sign"];
      sign = document.querySelector('.user-sign')
      sign.textContent = currentPlayer
    } else {

      const errorData = await response.json();
      if (errorData.message === "Game session is finished") {
          const cells = document.querySelectorAll('.cell');
          cells.forEach((cell) => {
            cell.style.pointerEvents = "none"
          })

      }
      console.log('Error:', errorData);
      console.error('Error:', response.status);
    }
  } catch (error) {
    console.error('Error:', error);
  }
});


function updateBoard(data) {

  if (data.hasOwnProperty('actual_board')) {
      data = data['actual_board'];
    }

  const cols = data[0].length;
  const board = document.querySelector('.board');
  const cells = board.querySelectorAll('.cell');

  // Iterate through the cells and update their text content
  cells.forEach((cell, index) => {
    const row = Math.floor(index / cols);
    const col = index % cols;
    cell.textContent = data[row][col] || '';
  });
}

function handleGameStatus(status, credits) {
  // Handle game status. If game is over, display the status and the new game button

  if (status != null) {
    const statusButton = document.querySelector('.status-button');
    if (status === 'You won') {
      statusButton.classList.remove('hidden');
      statusButton.textContent = 'You won';
      statusButton.classList.add('won');
      newGameButton = document.querySelector('.new-game-button');
      newGameButton.classList.remove('hidden');
      newGameButton.addEventListener('click', startNewGame);

    } else if (status === 'You lost') {
      statusButton.classList.remove('hidden');
      statusButton.textContent = 'You lost';
      statusButton.classList.add('lost');
      newGameButton = document.querySelector('.new-game-button');
      newGameButton.classList.remove('hidden');
      newGameButton.addEventListener('click', startNewGame);

    } else if (status === 'There is no winner') {
      let noWinner = document.querySelector('.no-winner');
      noWinner.classList.remove('hidden');
      newGameButton = document.querySelector('.new-game-button');
      newGameButton.classList.remove('hidden');
      newGameButton.addEventListener('click', startNewGame);
    }
    // Disable board interaction
    const cells = document.querySelectorAll('.cell');
    cells.forEach(cell => {
      cell.style.pointerEvents = 'none';
    });
  }
  updateCredits(credits);
}

newGameButton = document.querySelector('.new-game-button');
if (newGameButton != null){
  newGameButton.addEventListener('click', startNewGame);
}

function startNewGame() {
  // Clear the board
  const cells = document.querySelectorAll('.cell');
  cells.forEach(cell => {
    cell.textContent = '';
  });

  // Hide the status and new game buttons
  const statusButton = document.querySelector('.status-button');
  statusButton.classList.add('hidden');

  newGameButton.classList.add('hidden');

  // Enable board interaction
  cells.forEach(cell => {
    cell.style.pointerEvents = 'auto';
  });
  handleNewGame();
  // window.location.href = `/session_view/${sessionId}/game/${gameId}`;
}

function updateCredits(credits) {
  const creditsDiv = document.querySelector('.credits');
  creditsDiv.textContent = `Credits: ${credits}`;
}

async function handleNewGame() {
  try {
    const url = `http://localhost:8001/session/${sessionId}/game`;

    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + token
      }
    });
    if (response.ok) {
      const data = await response.json();
      if (data.game_details){
        const gameId = data.game_details.id;
        const sessionId= data.game_details.session_id;
        window.location.href = `/session_view/${sessionId}/game/${gameId}`;
      }

      console.log('Game started:', data);
    } else if (response.status === 400) {
      const errorData = await response.json();
      console.error('Bad Request:', errorData);
      // Extract session ID and unfinished game ID
      if (errorData) {
        const sessionID = errorData.session_id;
        const gameId = errorData.game_id;
        console.log(`/session_view/${sessionID}/game/${gameId}`)
        if (gameId) {
          window.location.href = `/session_view/${sessionID}/game/${gameId}`;
        } else {
          console.log('No unfinished games found.');
        }
      }
    } else {
      // Handle other error responses
      console.error('Error:', response.status);
    }
  } catch (error) {
    // Handle network or other errors
    console.error('Error:', error);
  }
}