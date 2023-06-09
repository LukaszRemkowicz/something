// Add an event listener to all the cells
const cells = document.querySelectorAll('.cell');
cells.forEach(cell => {
  cell.addEventListener('click', handleCellClick);
});

let row;
let col;


async function handleCellClick(event) {
  const cell = event.target;
  row = cell.dataset.row; // Retrieve the row value
  col = cell.dataset.col; // Retrieve the column value
  console.log('Clicked cell:', cell, 'Row:', row, 'Column:', col);

  if (cell.textContent === '') {
    cell.textContent = currentPlayer;
    cell.classList.add(currentPlayer);
    currentPlayer = currentPlayer === 'X' ? 'O' : 'X';

    // Call the function to communicate with the backend
    await sendMoveToBackend(row, col);
  }
}

async function sendMoveToBackend(index) {
  try {
    const token = getCookie('access_token');
    const url = `http://localhost:8001/session/${sessionId}/game/${gameId}`;
    console.log(url)

    const response = await fetch(url, {
      method: 'post',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + token
      },
      body: JSON.stringify({
        "row": parseInt(row),
        "col": parseInt(col)
      })
    });

    if (response.ok) {
      const data = await response.json();
      handleGameStatus(data.status, data.credits)
      updateBoard(data['actual_board']);
      update_score()
      // Handle the response from the backend
    } else {
      // Handle error response from the backend
      console.error('Error:', await response.json());
    }
  } catch (error) {
    // Handle network or other errors
    console.error('Error:', error);
  }
}
