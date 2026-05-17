// IDs of all right-panel sections — only one is visible at a time
const rightSectionIds = [
  'login-section',
  'admin-login',
  'student-login',
  'register-section'
];

// Fade an element in with a subtle slide-up animation
function fadeIn(el) {
  el.style.opacity = '0';
  el.style.transform = 'translateY(10px)';
  el.classList.remove('hidden');
  // Force a reflow so the CSS transition fires from the starting values above
  el.getBoundingClientRect();
  el.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
  el.style.opacity = '1';
  el.style.transform = 'translateY(0)';
}

// Hide every right-panel section by adding the 'hidden' class and clearing inline styles
function hideAllSections() {
  rightSectionIds.forEach((id) => {
    const el = document.getElementById(id);
    if (el) {
      el.style.transition = '';
      el.style.opacity = '';
      el.style.transform = '';
      el.classList.add('hidden');
    }
  });
}

// Show the login panel for the given role ('admin' or 'student')
function login(role) {
  hideAllSections();
  const target = role === 'admin' ? 'admin-login' : 'student-login';
  fadeIn(document.getElementById(target));
}

// Show the registration role-selection screen
function showRegistration() {
  hideAllSections();

  const registerSection = document.getElementById('register-section');
  // Hide both registration forms so only the role-selection cards are visible
  document.getElementById('admin-register').classList.add('hidden');
  document.getElementById('student-register').classList.add('hidden');
  document.querySelector('.register-options').classList.remove('hidden');

  // Show the section title and intro text
  const title = registerSection.querySelector('h2');
  const intro = registerSection.querySelector('p');
  title.classList.remove('hidden');
  intro.classList.remove('hidden');

  fadeIn(registerSection);
}

// Show the registration form for the given role ('admin' or 'student')
function showRegisterForm(role) {
  const registerSection = document.getElementById('register-section');
  const title = registerSection.querySelector('h2');
  const intro = registerSection.querySelector('p');

  // Hide the role-selection cards and section heading
  document.querySelector('.register-options').classList.add('hidden');
  title.classList.add('hidden');
  intro.classList.add('hidden');

  // Hide both forms first, then reveal the correct one
  const adminReg   = document.getElementById('admin-register');
  const studentReg = document.getElementById('student-register');
  adminReg.classList.add('hidden');
  studentReg.classList.add('hidden');

  const target = role === 'admin' ? adminReg : studentReg;
  // Small delay so the hide animation completes before the fade-in starts
  setTimeout(() => {
    target.style.opacity = '0';
    target.style.transform = 'translateY(8px)';
    target.classList.remove('hidden');
    target.getBoundingClientRect();
    target.style.transition = 'opacity 0.25s ease, transform 0.25s ease';
    target.style.opacity = '1';
    target.style.transform = 'translateY(0)';
  }, 10);
}

// Return to the main login role-selection screen
function backToMain() {
  hideAllSections();
  fadeIn(document.getElementById('login-section'));
}

// Called on DOMContentLoaded — decides which panel to show based on server-side state
function initView() {
  hideAllSections();

  // SERVER_LOGIN_TYPE is set by the Django template when a login attempt fails.
  // Re-open the correct login panel so the user sees the error and can try again.
  if (typeof SERVER_LOGIN_TYPE !== 'undefined' && SERVER_LOGIN_TYPE) {
    login(SERVER_LOGIN_TYPE);
    return;
  }

  // SERVER_SHOW_REGISTER is set when a registration form submission fails.
  // Re-open the registration section and show the correct form.
  if (typeof SERVER_SHOW_REGISTER !== 'undefined' && SERVER_SHOW_REGISTER) {
    const registerSection = document.getElementById('register-section');
    registerSection.classList.remove('hidden');

    // Hide the role-selection cards — go straight to the form that had errors
    document.querySelector('.register-options').classList.add('hidden');
    registerSection.querySelector('h2').classList.add('hidden');
    registerSection.querySelector('p').classList.add('hidden');

    if (typeof SERVER_SHOW_ADMIN_REG !== 'undefined' && SERVER_SHOW_ADMIN_REG) {
      // Admin registration form had errors — show it
      document.getElementById('admin-register').classList.remove('hidden');
      document.getElementById('student-register').classList.add('hidden');
    } else if (typeof SERVER_SHOW_STUDENT_REG !== 'undefined' && SERVER_SHOW_STUDENT_REG) {
      // Student registration form had errors — show it
      document.getElementById('student-register').classList.remove('hidden');
      document.getElementById('admin-register').classList.add('hidden');
    }
    return;
  }

  // Default: show the main login role-selection screen without animation
  document.getElementById('login-section').classList.remove('hidden');
}

window.addEventListener('DOMContentLoaded', initView);

// Client-side password match check for the admin registration form
function validateAdminRegister(event) {
  const password = document.getElementById('admin-password').value;
  const confirm  = document.getElementById('admin-confirm-password').value;
  const error    = document.getElementById('admin-password-error');

  if (password !== confirm) {
    error.style.display = 'block';
    document.getElementById('admin-confirm-password').focus();
    event.preventDefault(); // Stop the form from submitting
    return false;
  }

  error.style.display = 'none';
  return true;
}

// Client-side password match check for the student registration form
function validateStudentRegister(event) {
  const password = document.getElementById('student-password').value;
  const confirm  = document.getElementById('student-confirm-password').value;
  const error    = document.getElementById('student-password-error');

  if (password !== confirm) {
    error.style.display = 'block';
    document.getElementById('student-confirm-password').focus();
    event.preventDefault(); // Stop the form from submitting
    return false;
  }

  error.style.display = 'none';
  return true;
}
