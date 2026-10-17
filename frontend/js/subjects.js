/**
 * StudySync - Subjects Module
 */

let subjects = [];
let editingId = null;

const COLORS = [
  '#6366f1', // Indigo
  '#8b5cf6', // Violet
  '#ec4899', // Pink
  '#ef4444', // Red
  '#f59e0b', // Amber
  '#10b981', // Emerald
  '#06b6d4', // Cyan
  '#3b82f6'  // Blue
];

document.addEventListener('DOMContentLoaded', () => {
  requireAuth();
  loadUserInfo();
  setupLogout();
  setupModal();
  setupForm();
  loadSubjects();

  const addBtn = document.getElementById('add-subject-btn');
  if (addBtn) {
    addBtn.addEventListener('click', () => openModal(null));
  }
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
 * Fetch all subjects from the API
 */
async function loadSubjects() {
  const grid = document.getElementById('subjects-grid');
  if (grid) {
    grid.innerHTML = `
      <div class="skeleton" style="height: 160px;"></div>
      <div class="skeleton" style="height: 160px;"></div>
      <div class="skeleton" style="height: 160px;"></div>
    `;
  }

  try {
    const res = await apiRequest('GET', '/subjects/');
    if (res.ok) {
      subjects = await res.json();
      renderSubjects();
    } else {
      showToast('Error al cargar las materias', 'error');
    }
  } catch (error) {
    console.error('Failed to load subjects:', error);
    showToast('Error de conexión al cargar materias', 'error');
  }
}

/**
 * Render subject cards into the grid
 */
function renderSubjects() {
  const grid = document.getElementById('subjects-grid');
  if (!grid) return;

  if (!subjects || subjects.length === 0) {
    grid.innerHTML = `
      <div class="empty-state" style="grid-column: 1 / -1;">
        <div class="empty-state-title">No hay materias registradas</div>
        <div class="empty-state-desc">Comienza agregando las asignaturas correspondientes a tu período académico.</div>
        <button class="btn btn-primary" onclick="openModal()" style="margin-top: 1rem;">
          + Agregar Materia
        </button>
      </div>
    `;
    return;
  }

  grid.innerHTML = subjects.map(subject => {
    return `
      <div class="subject-card">
        <div>
          <div class="subject-card-header">
            <h3 class="subject-name">${escapeHtml(subject.name)}</h3>
          </div>

          <div class="subject-meta">
            ${subject.professor ? `
              <div class="subject-meta-item">
                <span class="meta-label">Docente:</span>
                <span>${escapeHtml(subject.professor)}</span>
              </div>
            ` : ''}
            ${subject.semester ? `
              <div class="subject-meta-item">
                <span class="meta-label">Semestre:</span>
                <span>${escapeHtml(subject.semester)}</span>
              </div>
            ` : ''}
          </div>
        </div>

        <div class="subject-actions">
          <button class="btn btn-outline btn-sm" onclick="openModal(${subject.id})" style="flex: 1;">
            Editar
          </button>
          <button class="btn btn-danger btn-sm" onclick="deleteSubject(${subject.id}, '${escapeHtml(subject.name).replace(/'/g, "\\'")}')" style="padding: 0.35rem 0.65rem;" title="Eliminar materia">
            Eliminar
          </button>
        </div>
      </div>
    `;
  }).join('');
}

/**
 * Initialize modal listeners and color picker
 */
function setupModal() {
  const modal = document.getElementById('subject-modal');
  const closeBtn = document.getElementById('modal-close');
  const cancelBtn = document.getElementById('modal-cancel');
  const colorPickerRow = document.getElementById('color-picker-row');

  // Render color options
  if (colorPickerRow) {
    colorPickerRow.innerHTML = COLORS.map(color => `
      <div class="color-option ${color === '#6366f1' ? 'selected' : ''}" 
           data-color="${color}" 
           style="background-color: ${color};" 
           onclick="selectColor('${color}')"
           title="${color}">
      </div>
    `).join('');
  }

  if (closeBtn) closeBtn.addEventListener('click', closeModal);
  if (cancelBtn) cancelBtn.addEventListener('click', closeModal);

  if (modal) {
    modal.addEventListener('click', (e) => {
      if (e.target === modal) closeModal();
    });
  }
}

/**
 * Open create/edit modal
 */
window.openModal = function (subjectId = null) {
  const modal = document.getElementById('subject-modal');
  const title = document.getElementById('modal-title');
  const nameInput = document.getElementById('subject-name');
  const profInput = document.getElementById('subject-professor');
  const semInput = document.getElementById('subject-semester');
  const colorInput = document.getElementById('selected-color');

  editingId = subjectId;

  if (editingId !== null) {
    const subject = subjects.find(s => s.id === editingId);
    if (subject) {
      if (title) title.textContent = 'Editar Materia';
      if (nameInput) nameInput.value = subject.name || '';
      if (profInput) profInput.value = subject.professor || '';
      if (semInput) semInput.value = subject.semester || '';
      const color = subject.color || '#6366f1';
      if (colorInput) colorInput.value = color;
      selectColor(color);
    }
  } else {
    if (title) title.textContent = 'Nueva Materia';
    if (nameInput) nameInput.value = '';
    if (profInput) profInput.value = '';
    if (semInput) semInput.value = '';
    const defaultColor = '#6366f1';
    if (colorInput) colorInput.value = defaultColor;
    selectColor(defaultColor);
  }

  if (modal) {
    modal.classList.add('show');
    if (nameInput) nameInput.focus();
  }
};

/**
 * Close subject modal
 */
function closeModal() {
  const modal = document.getElementById('subject-modal');
  if (modal) modal.classList.remove('show');
  editingId = null;
}

/**
 * Select a color for the subject
 */
window.selectColor = function (color) {
  const colorInput = document.getElementById('selected-color');
  if (colorInput) colorInput.value = color;

  const options = document.querySelectorAll('#color-picker-row .color-option');
  options.forEach(opt => {
    opt.classList.toggle('selected', opt.dataset.color === color);
  });
};

/**
 * Handle form submission for create / edit
 */
function setupForm() {
  const form = document.getElementById('subject-form');
  if (!form) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const submitBtn = form.querySelector('button[type="submit"]');
    const nameInput = document.getElementById('subject-name');
    const profInput = document.getElementById('subject-professor');
    const semInput = document.getElementById('subject-semester');
    const colorInput = document.getElementById('selected-color');

    const name = nameInput ? nameInput.value.trim() : '';
    const professor = profInput ? profInput.value.trim() : '';
    const semester = semInput ? semInput.value.trim() : '';
    const color = colorInput ? colorInput.value : '#6366f1';

    if (!name) {
      showToast('Por favor ingresa el nombre de la materia', 'error');
      return;
    }

    const payload = { name, professor, semester, color };
    setLoading(submitBtn, true);

    try {
      let res;
      if (editingId !== null) {
        res = await apiRequest('PUT', `/subjects/${editingId}`, payload);
      } else {
        res = await apiRequest('POST', '/subjects/', payload);
      }

      if (res.ok) {
        showToast(editingId !== null ? 'Materia actualizada' : 'Materia creada exitosamente');
        closeModal();
        await loadSubjects();
      } else {
        const data = await res.json().catch(() => ({}));
        showToast(data.detail || 'Error al guardar la materia', 'error');
      }
    } catch (err) {
      console.error('Error saving subject:', err);
      showToast('Error de conexión', 'error');
    } finally {
      setLoading(submitBtn, false);
    }
  });
}

/**
 * Delete a subject
 */
window.deleteSubject = async function (id, name) {
  if (!confirm(`¿Estás seguro de que deseas eliminar la materia "${name}"? Todas sus tareas asociadas podrían verse afectadas.`)) {
    return;
  }

  try {
    const res = await apiRequest('DELETE', `/subjects/${id}`);
    if (res.ok) {
      showToast('Materia eliminada exitosamente');
      await loadSubjects();
    } else {
      const data = await res.json().catch(() => ({}));
      showToast(data.detail || 'No se pudo eliminar la materia', 'error');
    }
  } catch (err) {
    console.error('Error deleting subject:', err);
    showToast('Error al intentar eliminar la materia', 'error');
  }
};

/**
 * Set button loading state
 */
function setLoading(btn, isLoading) {
  if (!btn) return;
  if (isLoading) {
    btn.dataset.prevHtml = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = `<span class="spinner"></span> <span>Guardando...</span>`;
  } else {
    btn.disabled = false;
    btn.innerHTML = btn.dataset.prevHtml || 'Guardar';
  }
}
