function getCookie(name) {
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

const token = getCookie('access_token'); // Retrieve the JWT token from the cookie
const sessionId = getCookie('sessionID'); // Retrieve the session ID from the cookie
const gameId = getCookie('unfinishedGameID'); // Retrieve the game ID from the cookie

const startSessionButton = document.querySelector('#startSessionBtn');
if (startSessionButton !== null) {
  startSessionButton.addEventListener('click', handleStartSession);
}

async function handleStartSession() {
  try {
    let url = 'http://localhost:8001/session';
    if (token){
      url += '?token=' + token;
    }

    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + token
      },
    });
    if (response.ok) {
      // Handle successful response
      const data = await response.json();
    } else if (response.status === 400) {
      // Handle specific error case (400 Bad Request)
      const errorData = await response.json();
      console.error('Bad Request:', errorData.error);

      // Extract session ID and unfinished game ID
      if (errorData.session_detail) {
        const sessionID = errorData.session_detail.id;
        const unfinishedGame = errorData.session_detail.games.find(game => game.status !== 'finished');
        console.log(errorData)
        if (unfinishedGame) {
          const unfinishedGameID = unfinishedGame.id;
          console.log('Session ID:', sessionID);
          console.log('Unfinished Game ID:', unfinishedGameID);
          console.log(`/session_view/${sessionID}/game/${unfinishedGameID}`);
          window.location.href = `/session_view/${sessionID}/game/${unfinishedGameID}`;
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
