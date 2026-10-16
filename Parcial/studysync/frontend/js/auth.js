/**
 * StudySync - Authentication & OTP Verification Logic
 */

document.addEventListener('DOMContentLoaded', () => {
  // If already logged in, redirect straight to dashboard
  if (localStorage.getItem('access_token')) {
    window.location.href = '/dashboard';
    return;
  }

  setupTabs();
  setupLoginForm();
  setupRegisterForm();
  setupOtpForm();
});

/**
 * Tab switcher between Login and Register views
 */
function setupTabs() {
  const tabs = document.querySelectorAll('.tab-btn');
  const loginStep = document.getElementById('step-login');
  const registerStep = document.getElementById('step-register');
  const otpStep = document.getElementById('step-otp');
  const authTabsContainer = document.querySelector('.auth-tabs');

  window.switchTab = function (tabName) {
    tabs.forEach(tab => {
      tab.classList.toggle('active', tab.dataset.tab === tabName);
    });

    if (authTabsContainer) authTabsContainer.style.display = 'flex';

    if (loginStep) loginStep.classList.toggle('active', tabName === 'login');
    if (registerStep) registerStep.classList.toggle('active', tabName === 'register');
    if (otpStep) otpStep.classList.remove('active');

    hideAlert('login-alert');
    hideAlert('register-alert');
    hideAlert('otp-alert');
  };

  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      window.switchTab(tab.dataset.tab);
    });
  });

  // Links within forms that switch tabs
  const toRegisterLinks = document.querySelectorAll('.go-to-register');
  toRegisterLinks.forEach(link => {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      window.switchTab('register');
    });
  });

  const toLoginLinks = document.querySelectorAll('.go-to-login');
  toLoginLinks.forEach(link => {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      window.switchTab('login');
    });
  });
}

/**
 * Handle user login
 */
function setupLoginForm() {
  const form = document.getElementById('login-form');
  if (!form) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    hideAlert('login-alert');

    const submitBtn = form.querySelector('button[type="submit"]');
    const emailInput = document.getElementById('login-email');
    const passwordInput = document.getElementById('login-password');

    const email = emailInput ? emailInput.value.trim() : '';
    const password = passwordInput ? passwordInput.value : '';

    if (!email || !password) {
      showAlert('login-alert', 'Por favor ingresa tu correo y contraseña.', 'error');
      return;
    }

    setLoading(submitBtn, true);

    try {
      const response = await apiRequest('POST', '/auth/login', { email, password }, false);
      let data = {};
      try {
        data = await response.json();
      } catch {
        data = {};
      }

      if (response.ok) {
        localStorage.setItem('access_token', data.access_token);
        if (data.refresh_token) {
          localStorage.setItem('refresh_token', data.refresh_token);
        }

        // Store user payload if returned directly or fetch /me
        if (data.user) {
          localStorage.setItem('user', JSON.stringify(data.user));
          window.location.href = '/dashboard';
        } else {
          try {
            const meRes = await apiRequest('GET', '/auth/me', null, true);
            if (meRes.ok) {
              const me = await meRes.json();
              localStorage.setItem('user', JSON.stringify(me));
            } else {
              localStorage.setItem('user', JSON.stringify({ email }));
            }
          } catch {
            localStorage.setItem('user', JSON.stringify({ email }));
          }
          window.location.href = '/dashboard';
        }
      } else {
        let errorMsg = 'Credenciales inválidas. Verifica tus datos.';
        if (typeof data.detail === 'string') {
          errorMsg = data.detail;
        } else if (Array.isArray(data.detail) && data.detail.length > 0) {
          errorMsg = data.detail.map(d => d.msg || JSON.stringify(d)).join('. ');
        } else if (data.message) {
          errorMsg = data.message;
        } else if (response.status >= 500) {
          errorMsg = 'Error en el servidor. Por favor intenta de nuevo.';
        }

        if (errorMsg.toLowerCase().includes('no verificada')) {
          showAlert(
            'login-alert',
            `Cuenta no verificada. <a href="#" id="verify-now-btn" style="color: inherit; text-decoration: underline; font-weight: 600; margin-left: 5px;">Ingresar código OTP aquí</a>`,
            'error',
            true
          );
          const verifyBtn = document.getElementById('verify-now-btn');
          if (verifyBtn) {
            verifyBtn.addEventListener('click', (ev) => {
              ev.preventDefault();
              sessionStorage.setItem('pending_email', email);
              switchToOtpStep();
            });
          }
        } else {
          showAlert('login-alert', errorMsg, 'error');
        }
      }
    } catch (err) {
      showAlert('login-alert', 'Error de conexión. Inténtalo de nuevo más tarde.', 'error');
    } finally {
      setLoading(submitBtn, false);
    }
  });
}

/**
 * Handle user registration
 */
function setupRegisterForm() {
  const form = document.getElementById('register-form');
  if (!form) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    hideAlert('register-alert');

    const submitBtn = form.querySelector('button[type="submit"]');
    const nameInput = document.getElementById('register-name');
    const emailInput = document.getElementById('register-email');
    const passwordInput = document.getElementById('register-password');

    const name = nameInput ? nameInput.value.trim() : '';
    const email = emailInput ? emailInput.value.trim() : '';
    const password = passwordInput ? passwordInput.value : '';

    if (!name || !email || !password) {
      showAlert('register-alert', 'Por favor completa todos los campos requeridos.', 'error');
      return;
    }

    if (password.length < 8) {
      showAlert('register-alert', 'La contraseña debe tener al menos 8 caracteres.', 'error');
      return;
    }

    if (!/\d/.test(password)) {
      showAlert('register-alert', 'La contraseña debe contener al menos un número.', 'error');
      return;
    }

    setLoading(submitBtn, true);

    try {
      const response = await apiRequest('POST', '/auth/register', { name, email, password }, false);
      let data = {};
      try {
        data = await response.json();
      } catch {
        data = {};
      }

      if (response.ok) {
        sessionStorage.setItem('pending_email', email);
        switchToOtpStep();
      } else {
        let errorMsg = 'No fue posible registrar la cuenta.';
        if (typeof data.detail === 'string') {
          errorMsg = data.detail;
        } else if (Array.isArray(data.detail) && data.detail.length > 0) {
          errorMsg = data.detail.map(d => d.msg || JSON.stringify(d)).join('. ');
        } else if (data.message) {
          errorMsg = data.message;
        } else if (response.status >= 500) {
          errorMsg = 'Error interno del servidor. Revisa los registros.';
        }
        showAlert('register-alert', errorMsg, 'error');
      }
    } catch (err) {
      showAlert('register-alert', 'Error de conexión con el servidor.', 'error');
    } finally {
      setLoading(submitBtn, false);
    }
  });
}

/**
 * Switches UI to OTP verification view
 */
function switchToOtpStep() {
  const authTabsContainer = document.querySelector('.auth-tabs');
  const loginStep = document.getElementById('step-login');
  const registerStep = document.getElementById('step-register');
  const otpStep = document.getElementById('step-otp');
  const emailDisplay = document.getElementById('otp-email-display');

  if (authTabsContainer) authTabsContainer.style.display = 'none';
  if (loginStep) loginStep.classList.remove('active');
  if (registerStep) registerStep.classList.remove('active');

  const pendingEmail = sessionStorage.getItem('pending_email') || '';
  if (emailDisplay) emailDisplay.textContent = pendingEmail;

  if (otpStep) {
    otpStep.classList.add('active');
    hideAlert('otp-alert');
    showAlert('otp-alert', `Se ha enviado un código de verificación a ${pendingEmail}`, 'info');

    // Reset digit inputs and focus first
    const digits = otpStep.querySelectorAll('.otp-digit');
    digits.forEach(d => (d.value = ''));
    if (digits.length > 0) digits[0].focus();
  }
}

/**
 * Handles OTP digit inputs, verification submit and resend
 */
function setupOtpForm() {
  const digits = Array.from(document.querySelectorAll('.otp-digit'));
  const otpForm = document.getElementById('otp-form');
  const resendBtn = document.getElementById('resend-otp-btn');
  const backBtn = document.getElementById('otp-back-btn');

  // Input navigation: auto-advance, backspace navigation, paste handling
  digits.forEach((digit, index) => {
    digit.addEventListener('input', (e) => {
      const val = e.target.value;
      if (val.length >= 1) {
        // Keep single character
        digit.value = val.slice(-1);
        if (index < digits.length - 1) {
          digits[index + 1].focus();
        }
      }
    });

    digit.addEventListener('keydown', (e) => {
      if (e.key === 'Backspace' && !digit.value && index > 0) {
        digits[index - 1].focus();
      }
    });

    digit.addEventListener('paste', (e) => {
      e.preventDefault();
      const pasteData = (e.clipboardData || window.clipboardData).getData('text').trim();
      if (!pasteData) return;

      const chars = pasteData.replace(/\s+/g, '').slice(0, digits.length).split('');
      chars.forEach((char, i) => {
        if (digits[i]) digits[i].value = char;
      });

      const nextFocus = Math.min(chars.length, digits.length - 1);
      digits[nextFocus].focus();
    });
  });

  // Submit OTP Verification
  if (otpForm) {
    otpForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      hideAlert('otp-alert');

      const submitBtn = otpForm.querySelector('button[type="submit"]');
      const code = digits.map(d => d.value.trim()).join('');
      const email = sessionStorage.getItem('pending_email');

      if (!email) {
        showAlert('otp-alert', 'No hay un correo electrónico pendiente de verificación.', 'error');
        return;
      }

      if (code.length < digits.length) {
        showAlert('otp-alert', `Por favor ingresa los ${digits.length} dígitos del código.`, 'error');
        return;
      }

      setLoading(submitBtn, true);

      try {
        const response = await apiRequest('POST', '/auth/verify-otp', {
          email,
          otp: code,
          code: code
        }, false);

        let data = {};
        try {
          data = await response.json();
        } catch {
          data = {};
        }

        if (response.ok) {
          showAlert('otp-alert', '¡Cuenta verificada exitosamente! Redirigiendo al inicio de sesión...', 'success');
          setTimeout(() => {
            sessionStorage.removeItem('pending_email');
            window.switchTab('login');
          }, 2000);
        } else {
          let errorMsg = 'El código es inválido o ha expirado.';
          if (typeof data.detail === 'string') {
            errorMsg = data.detail;
          } else if (Array.isArray(data.detail) && data.detail.length > 0) {
            errorMsg = data.detail.map(d => d.msg || JSON.stringify(d)).join('. ');
          } else if (data.message) {
            errorMsg = data.message;
          }
          showAlert('otp-alert', errorMsg, 'error');
        }
      } catch (err) {
        showAlert('otp-alert', 'Error al verificar el código.', 'error');
      } finally {
        setLoading(submitBtn, false);
      }
    });
  }

  // Resend OTP Code
  if (resendBtn) {
    resendBtn.addEventListener('click', async (e) => {
      e.preventDefault();
      hideAlert('otp-alert');

      const email = sessionStorage.getItem('pending_email');
      if (!email) {
        showAlert('otp-alert', 'No hay un correo registrado para reenviar código.', 'error');
        return;
      }

      resendBtn.disabled = true;
      const originalText = resendBtn.textContent;
      resendBtn.textContent = 'Enviando...';

      try {
        const response = await apiRequest('POST', '/auth/resend-otp', { email }, false);
        const data = await response.json();

        if (response.ok) {
          showAlert('otp-alert', 'Código de verificación reenviado exitosamente.', 'info');
        } else {
          const errorMsg = data.detail || data.message || 'No se pudo reenviar el código.';
          showAlert('otp-alert', errorMsg, 'error');
        }
      } catch (err) {
        showAlert('otp-alert', 'Error de red al reenviar el código.', 'error');
      } finally {
        setTimeout(() => {
          resendBtn.disabled = false;
          resendBtn.textContent = originalText;
        }, 5000);
      }
    });
  }

  // Back button to return to login
  if (backBtn) {
    backBtn.addEventListener('click', (e) => {
      e.preventDefault();
      window.switchTab('login');
    });
  }
}

/**
 * Display alert banner inside a container
 */
function showAlert(id, message, type = 'error', isHtml = false) {
  const alertEl = document.getElementById(id);
  if (!alertEl) return;
  alertEl.className = `alert alert-${type} show`;
  if (isHtml) {
    alertEl.innerHTML = message;
  } else {
    alertEl.textContent = message;
  }
}

/**
 * Hide alert banner
 */
function hideAlert(id) {
  const alertEl = document.getElementById(id);
  if (alertEl) {
    alertEl.className = 'alert';
    alertEl.textContent = '';
  }
}

/**
 * Loading state wrapper for auth buttons
 */
function setLoading(btn, isLoading) {
  if (!btn) return;
  if (isLoading) {
    btn.dataset.prevHtml = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = `<span class="spinner"></span> <span>Procesando...</span>`;
  } else {
    btn.disabled = false;
    btn.innerHTML = btn.dataset.prevHtml || 'Continuar';
  }
}
