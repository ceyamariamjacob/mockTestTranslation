export function login(): boolean {
  const usernameInput = document.getElementById('username') as HTMLInputElement;
  const passwordInput = document.getElementById('password') as HTMLInputElement;
  const message = document.getElementById('message');

  const username = usernameInput?.value;
  const password = passwordInput?.value;

  if (username === 'ceya' && password === 'pass') {
    if (message) message.textContent = 'Login successful';
    return true;
  } else {
    if (message) message.textContent = 'Invalid credentials';
    return false;
  }
}
