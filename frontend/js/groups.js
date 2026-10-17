/**
 * StudySync - Study Groups Module
 */

let groups = [];

document.addEventListener('DOMContentLoaded', () => {
  requireAuth();
  loadUserInfo();
  setupLogout();
  setupCreateModal();
  setupJoinModal();
  setupMembersModal();
  loadGroups();
});

/**
 * Handle user logout across pages
 */
function setupLogout() {
  const logoutBtn = document.getElementById('logout-btn');
  if (logoutBtn) {
    logoutBtn.addEventListener('click', async (e) => {
      e.preventDefault();
      try {
        await apiRequest('POST', '/auth/logout', null, true);
      } catch (err) {
        console.error('Logout error:', err);
      } finally {
        localStorage.clear();
        sessionStorage.clear();
        window.location.href = '/';
      }
    });
  }
}

/**
 * Fetch user's study groups
 */
async function loadGroups() {
  const grid = document.getElementById('groups-grid');
  if (grid) {
    grid.innerHTML = `
      <div class="skeleton" style="height: 180px;"></div>
      <div class="skeleton" style="height: 180px;"></div>
    `;
  }

  try {
    const res = await apiRequest('GET', '/groups/');
    if (res.ok) {
      groups = await res.json();
      renderGroups();
    } else {
      showToast('Error al cargar grupos de estudio', 'error');
    }
  } catch (err) {
    console.error('Failed to load groups:', err);
    showToast('Error de red al cargar grupos', 'error');
  }
}

/**
 * Render study group cards
 */
function renderGroups() {
  const grid = document.getElementById('groups-grid');
  if (!grid) return;

  if (!groups || groups.length === 0) {
    grid.innerHTML = `
      <div class="empty-state" style="grid-column: 1 / -1;">
        <div class="empty-state-title">No perteneces a ningún grupo</div>
        <div class="empty-state-desc">Crea un grupo de estudio con tus compañeros o únete a uno mediante un código de invitación.</div>
        <div style="display: flex; gap: 0.75rem; margin-top: 1.25rem;">
          <button class="btn btn-primary" onclick="openCreateModal()">+ Crear Grupo</button>
          <button class="btn btn-outline" onclick="openJoinModal()">Unirse con código</button>
        </div>
      </div>
    `;
    return;
  }

  grid.innerHTML = groups.map(group => {
    const inviteCode = group.invite_code || group.code || '------';
    const escapedName = escapeHtml(group.name).replace(/'/g, "\\'");
    return `
      <div class="group-card" id="group-card-${group.id}">
        <div class="group-card-header">
          <h3 class="group-name">${escapeHtml(group.name)}</h3>
          <span class="badge badge-subject">Grupo</span>
        </div>

        <p class="group-description">
          ${escapeHtml(group.description || 'Sin descripción')}
        </p>

        <div class="invite-code-box">
          <div>
            <div class="invite-code-label">Código de invitación</div>
            <div class="invite-code">${escapeHtml(inviteCode)}</div>
          </div>
          <button class="copy-btn" onclick="copyCode('${escapeHtml(inviteCode)}')" title="Copiar código">
            Copiar
          </button>
        </div>

        <div class="group-actions">
          <button class="btn btn-outline btn-sm" onclick="viewMembers(${group.id}, '${escapedName}')" style="flex: 1;">
            Ver miembros
          </button>
          <button class="btn btn-danger btn-sm" onclick="leaveGroup(${group.id}, '${escapedName}')" title="Salir del grupo">
            Salir
          </button>
        </div>
      </div>
    `;
  }).join('');
}

/**
 * Copy invitation code to clipboard
 */
window.copyCode = function (code) {
  if (!code || code === '------') return;
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(code).then(() => {
      showToast('¡Código copiado al portapapeles!', 'info');
    }).catch(() => {
      fallbackCopy(code);
    });
  } else {
    fallbackCopy(code);
  }
};

function fallbackCopy(code) {
  const textArea = document.createElement('textarea');
  textArea.value = code;
  textArea.style.position = 'fixed';
  textArea.style.left = '-9999px';
  document.body.appendChild(textArea);
  textArea.focus();
  textArea.select();
  try {
    document.execCommand('copy');
    showToast('¡Código copiado al portapapeles!', 'info');
  } catch (e) {
    showToast(`Código: ${code}`, 'info');
  }
  document.body.removeChild(textArea);
}

/**
 * Create Group Modal logic
 */
function setupCreateModal() {
  const modal = document.getElementById('create-group-modal');
  const openBtn = document.getElementById('create-group-btn');
  const closeBtn = document.getElementById('create-group-close');
  const cancelBtn = document.getElementById('create-group-cancel');
  const form = document.getElementById('create-group-form');

  window.openCreateModal = function () {
    if (form) form.reset();
    if (modal) {
      modal.classList.add('show');
      const input = document.getElementById('group-name-input');
      if (input) input.focus();
    }
  };

  window.closeCreateModal = function () {
    if (modal) modal.classList.remove('show');
  };

  if (openBtn) openBtn.addEventListener('click', window.openCreateModal);
  if (closeBtn) closeBtn.addEventListener('click', window.closeCreateModal);
  if (cancelBtn) cancelBtn.addEventListener('click', window.closeCreateModal);

  if (modal) {
    modal.addEventListener('click', (e) => {
      if (e.target === modal) window.closeCreateModal();
    });
  }

  if (form) {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const submitBtn = form.querySelector('button[type="submit"]');
      const nameInput = document.getElementById('group-name-input');
      const descInput = document.getElementById('group-desc-input');

      const name = nameInput ? nameInput.value.trim() : '';
      const description = descInput ? descInput.value.trim() : '';

      if (!name) {
        showToast('El nombre del grupo es obligatorio', 'error');
        return;
      }

      setLoading(submitBtn, true);

      try {
        const res = await apiRequest('POST', '/groups/', { name, description });
        if (res.ok) {
          showToast('Grupo creado exitosamente');
          window.closeCreateModal();
          await loadGroups();
        } else {
          const err = await res.json().catch(() => ({}));
          showToast(err.detail || 'Error al crear el grupo', 'error');
        }
      } catch (err) {
        console.error('Error creating group:', err);
        showToast('Error de red al crear grupo', 'error');
      } finally {
        setLoading(submitBtn, false);
      }
    });
  }
}

/**
 * Join Group Modal logic
 */
function setupJoinModal() {
  const modal = document.getElementById('join-group-modal');
  const openBtn = document.getElementById('join-group-btn');
  const closeBtn = document.getElementById('join-group-close');
  const cancelBtn = document.getElementById('join-group-cancel');
  const form = document.getElementById('join-group-form');

  window.openJoinModal = function () {
    if (form) form.reset();
    if (modal) {
      modal.classList.add('show');
      const input = document.getElementById('join-code');
      if (input) input.focus();
    }
  };

  window.closeJoinModal = function () {
    if (modal) modal.classList.remove('show');
  };

  if (openBtn) openBtn.addEventListener('click', window.openJoinModal);
  if (closeBtn) closeBtn.addEventListener('click', window.closeJoinModal);
  if (cancelBtn) cancelBtn.addEventListener('click', window.closeJoinModal);

  if (modal) {
    modal.addEventListener('click', (e) => {
      if (e.target === modal) window.closeJoinModal();
    });
  }

  if (form) {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const submitBtn = form.querySelector('button[type="submit"]');
      const codeInput = document.getElementById('join-code');
      const rawCode = codeInput ? codeInput.value : '';
      const inviteCode = rawCode.toUpperCase().trim();

      if (!inviteCode) {
        showToast('Por favor introduce el código de invitación', 'error');
        return;
      }

      setLoading(submitBtn, true);

      try {
        const res = await apiRequest('POST', '/groups/join', {
          invite_code: inviteCode,
          code: inviteCode
        });

        if (res.ok) {
          showToast('¡Te has unido al grupo exitosamente!');
          window.closeJoinModal();
          await loadGroups();
        } else {
          const err = await res.json().catch(() => ({}));
          showToast(err.detail || 'Código de invitación no válido o expirado', 'error');
        }
      } catch (err) {
        console.error('Error joining group:', err);
        showToast('Error de red al unirse al grupo', 'error');
      } finally {
        setLoading(submitBtn, false);
      }
    });
  }
}

/**
 * View group members
 */
function setupMembersModal() {
  const modal = document.getElementById('members-modal');
  const closeBtn = document.getElementById('members-modal-close');

  if (closeBtn) {
    closeBtn.addEventListener('click', () => {
      if (modal) modal.classList.remove('show');
    });
  }

  if (modal) {
    modal.addEventListener('click', (e) => {
      if (e.target === modal) modal.classList.remove('show');
    });
  }
}

window.viewMembers = async function (groupId, groupName) {
  const modal = document.getElementById('members-modal');
  const title = document.getElementById('members-modal-title');
  const listContainer = document.getElementById('members-list');

  if (title) title.textContent = `Miembros de ${groupName}`;
  if (listContainer) {
    listContainer.innerHTML = `
      <div class="skeleton" style="height: 50px; margin-bottom: 0.5rem;"></div>
      <div class="skeleton" style="height: 50px;"></div>
    `;
  }

  if (modal) modal.classList.add('show');

  try {
    const res = await apiRequest('GET', `/groups/${groupId}/members`);
    if (res.ok) {
      const members = await res.json();
      if (!members || members.length === 0) {
        listContainer.innerHTML = `<div class="empty-state" style="padding: 1.5rem;"><p>No se encontraron miembros en este grupo.</p></div>`;
        return;
      }

      listContainer.innerHTML = members.map(m => {
        const name = m.name || m.email || 'Usuario';
        const initial = name.charAt(0).toUpperCase();
        const role = m.role ? `<span class="badge badge-subject" style="margin-left: auto;">${escapeHtml(m.role)}</span>` : '';
        return `
          <div class="member-item">
            <div class="member-avatar">${initial}</div>
            <div class="member-info">
              <span class="member-name">${escapeHtml(name)}</span>
              <span class="member-email">${escapeHtml(m.email || '')}</span>
            </div>
            ${role}
          </div>
        `;
      }).join('');
    } else {
      listContainer.innerHTML = `<p style="color: var(--color-danger); text-align: center; padding: 1rem;">No se pudieron cargar los miembros.</p>`;
    }
  } catch (err) {
    console.error('Error fetching members:', err);
    if (listContainer) {
      listContainer.innerHTML = `<p style="color: var(--color-danger); text-align: center; padding: 1rem;">Error de red.</p>`;
    }
  }
};

/**
 * Leave a group
 */
window.leaveGroup = async function (groupId, groupName) {
  if (!confirm(`¿Estás seguro de que deseas salir del grupo "${groupName}"?`)) {
    return;
  }

  try {
    const res = await apiRequest('DELETE', `/groups/${groupId}/leave`);
    if (res.ok) {
      showToast(`Has salido de "${groupName}"`);
      await loadGroups();
    } else {
      const err = await res.json().catch(() => ({}));
      showToast(err.detail || 'No fue posible salir del grupo', 'error');
    }
  } catch (err) {
    console.error('Error leaving group:', err);
    showToast('Error de red al salir del grupo', 'error');
  }
};

/**
 * Button loading state
 */
function setLoading(btn, isLoading) {
  if (!btn) return;
  if (isLoading) {
    btn.dataset.prevHtml = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = `<span class="spinner"></span> <span>Procesando...</span>`;
  } else {
    btn.disabled = false;
    btn.innerHTML = btn.dataset.prevHtml || 'Aceptar';
  }
}
