document.querySelector('#loginForm').addEventListener('submit', async function(event) {
  event.preventDefault();

  const email = document.querySelector('#email').value;
  const password = document.querySelector('#password').value;

  try {
    const response = await fetch('http://localhost:8001/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ email, password })
    });

    if (response.ok) {
      const data = await response.json();
      const token = data.access_token;
      // Save the access token in a cookie
      document.cookie = `access_token=${token}; path=/`;
      window.location.href = '/session_view?token=' + encodeURIComponent(token);
    } else {
      console.error('Error:', response.status);
    }
  } catch (error) {
    console.error('Error:', error);
  }
});
