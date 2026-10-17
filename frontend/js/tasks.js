/**
 * StudySync - Tasks Management Module
 */

let tasks = [];
let subjects = [];
let editingTaskId = null;
let currentFilters = {
  subject_id: '',
  status: '',
  priority: ''
};

document.addEventListener('DOMContentLoaded', () => {
  requireAuth();
  loadUserInfo();
  setupLogout();
  setupFilters();
  setupModal();
  setupForm();

  const addBtn = document.getElementById('add-task-btn');
  if (addBtn) {
    addBtn.addEventListener('click', () => openTaskModal(null));
  }

  // Initial load
  loadSubjects().then(() => {
    loadTasks();
  });
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
 * Fetch subjects and populate filter and form dropdowns
 */
async function loadSubjects() {
  try {
    const res = await apiRequest('GET', '/subjects/');
    if (res.ok) {
      subjects = await res.json();
      populateSubjectDropdowns();
    }
  } catch (err) {
    console.error('Failed to load subjects for tasks:', err);
  }
}

/**
 * Fill subject options into select elements
 */
function populateSubjectDropdowns() {
  const filterSelect = document.getElementById('filter-subject');
  const taskSubjectSelect = document.getElementById('task-subject');

  if (filterSelect) {
    const currentVal = filterSelect.value;
    filterSelect.innerHTML = `<option value="">Todas las materias</option>` +
      subjects.map(s => `<option value="${s.id}">${escapeHtml(s.name)}</option>`).join('');
    filterSelect.value = currentVal;
  }

  if (taskSubjectSelect) {
    taskSubjectSelect.innerHTML = `<option value="">Sin materia asignada</option>` +
      subjects.map(s => `<option value="${s.id}">${escapeHtml(s.name)}</option>`).join('');
  }
}

/**
 * Fetch tasks based on active filters
 */
async function loadTasks() {
  const listContainer = document.getElementById('tasks-list');
  if (listContainer) {
    listContainer.innerHTML = `
      <div class="skeleton" style="height: 64px; margin-bottom: 0.75rem;"></div>
      <div class="skeleton" style="height: 64px; margin-bottom: 0.75rem;"></div>
      <div class="skeleton" style="height: 64px; margin-bottom: 0.75rem;"></div>
    `;
  }

  const queryParams = new URLSearchParams();
  if (currentFilters.subject_id) queryParams.append('subject_id', currentFilters.subject_id);
  if (currentFilters.status) queryParams.append('status', currentFilters.status);
  if (currentFilters.priority) queryParams.append('priority', currentFilters.priority);

  const queryString = queryParams.toString() ? `?${queryParams.toString()}` : '';

  try {
    const res = await apiRequest('GET', `/tasks/${queryString}`);
    if (res.ok) {
      tasks = await res.json();
      renderTasks();
    } else {
      showToast('Error al cargar las tareas', 'error');
    }
  } catch (err) {
    console.error('Error fetching tasks:', err);
    showToast('Error de conexión al cargar tareas', 'error');
  }
}

/**
 * Render task list
 */
function renderTasks() {
  const listContainer = document.getElementById('tasks-list');
  if (!listContainer) return;

  if (!tasks || tasks.length === 0) {
    listContainer.innerHTML = `
      <div class="empty-state">
        
        <div class="empty-state-title">No hay tareas encontradas</div>
        <div class="empty-state-desc">No se encontraron tareas con los filtros seleccionados. Crea una nueva tarea para comenzar.</div>
        <button class="btn btn-primary" onclick="openTaskModal()" style="margin-top: 1rem;">
          + Nueva Tarea
        </button>
      </div>
    `;
    return;
  }

  const subjectMap = {};
  subjects.forEach(s => { subjectMap[s.id] = s; });

  listContainer.innerHTML = tasks.map(task => {
    const subj = subjectMap[task.subject_id];
    const isTaskOverdue = isOverdue(task.due_date) && task.status !== 'done';
    const statusClass = task.status === 'done' ? 'done' : task.status === 'in_progress' ? 'in_progress' : 'pending';
    const isCompleted = task.status === 'done';

    return `
      <div class="task-item ${isCompleted ? 'completed' : ''}" id="task-item-${task.id}">
        <div class="task-checkbox ${statusClass}" 
             onclick="cycleStatus(${task.id}, '${task.status}')" 
             title="Cambiar estado (actual: ${getStatusLabel(task.status)})">
          ${task.status === 'done' ? '✓' : task.status === 'in_progress' ? '●' : ''}
        </div>

        <div class="task-content">
          <span class="task-title">${escapeHtml(task.title)}</span>
          ${task.description ? `<p class="task-description">${escapeHtml(task.description)}</p>` : ''}
          <div class="task-meta">
            ${subj ? `<span class="badge badge-subject">${escapeHtml(subj.name)}</span>` : ''}
            <span class="badge badge-${task.priority || 'medium'}">${getPriorityLabel(task.priority)}</span>
            <span class="badge badge-${statusClass}">${getStatusLabel(task.status)}</span>
            <span class="due-date ${isTaskOverdue ? 'overdue' : ''}">
              ${formatDate(task.due_date)} ${isTaskOverdue ? '(Vencida)' : ''}
            </span>
          </div>
        </div>

        <div class="task-actions">
          <button class="btn btn-outline btn-sm" onclick="openTaskModal(${task.id})" title="Editar tarea">
            Editar
          </button>
          <button class="btn btn-danger btn-sm" onclick="deleteTask(${task.id})" title="Eliminar tarea">
            Eliminar
          </button>
        </div>
      </div>
    `;
  }).join('');
}

/**
 * Cycle task status: pending -> in_progress -> done -> pending
 */
window.cycleStatus = async function (taskId, currentStatus) {
  const statusCycle = {
    pending: 'in_progress',
    in_progress: 'done',
    done: 'pending'
  };

  const nextStatus = statusCycle[currentStatus] || 'in_progress';

  try {
    const res = await apiRequest('PATCH', `/tasks/${taskId}/status`, { status: nextStatus });
    if (res.ok) {
      // Update local task list
      const task = tasks.find(t => t.id === taskId);
      if (task) {
        task.status = nextStatus;
      }
      renderTasks();
      showToast(`Estado cambiado a: ${getStatusLabel(nextStatus)}`, 'info');
    } else {
      showToast('No fue posible actualizar el estado', 'error');
    }
  } catch (err) {
    console.error('Error changing task status:', err);
    showToast('Error de red al cambiar estado', 'error');
  }
};

/**
 * Setup change listeners on filter inputs
 */
function setupFilters() {
  const subjectFilter = document.getElementById('filter-subject');
  const statusFilter = document.getElementById('filter-status');
  const priorityFilter = document.getElementById('filter-priority');

  if (subjectFilter) {
    subjectFilter.addEventListener('change', (e) => {
      currentFilters.subject_id = e.target.value;
      loadTasks();
    });
  }

  if (statusFilter) {
    statusFilter.addEventListener('change', (e) => {
      currentFilters.status = e.target.value;
      loadTasks();
    });
  }

  if (priorityFilter) {
    priorityFilter.addEventListener('change', (e) => {
      currentFilters.priority = e.target.value;
      loadTasks();
    });
  }
}

/**
 * Modal handling
 */
function setupModal() {
  const modal = document.getElementById('task-modal');
  const closeBtn = document.getElementById('task-modal-close');
  const cancelBtn = document.getElementById('task-modal-cancel');

  if (closeBtn) closeBtn.addEventListener('click', closeTaskModal);
  if (cancelBtn) cancelBtn.addEventListener('click', closeTaskModal);

  if (modal) {
    modal.addEventListener('click', (e) => {
      if (e.target === modal) closeTaskModal();
    });
  }
}

window.openTaskModal = function (taskId = null) {
  const modal = document.getElementById('task-modal');
  const titleEl = document.getElementById('task-modal-title');
  const titleInput = document.getElementById('task-title-input');
  const descInput = document.getElementById('task-description');
  const dueDateInput = document.getElementById('task-due-date');
  const prioritySelect = document.getElementById('task-priority');
  const subjectSelect = document.getElementById('task-subject');

  editingTaskId = taskId;

  if (editingTaskId !== null) {
    const task = tasks.find(t => t.id === editingTaskId);
    if (task) {
      if (titleEl) titleEl.textContent = 'Editar Tarea';
      if (titleInput) titleInput.value = task.title || '';
      if (descInput) descInput.value = task.description || '';
      if (dueDateInput) {
        dueDateInput.value = task.due_date ? task.due_date.split('T')[0] : '';
      }
      if (prioritySelect) prioritySelect.value = task.priority || 'medium';
      if (subjectSelect) subjectSelect.value = task.subject_id || '';
    }
  } else {
    if (titleEl) titleEl.textContent = 'Nueva Tarea';
    if (titleInput) titleInput.value = '';
    if (descInput) descInput.value = '';
    if (dueDateInput) dueDateInput.value = '';
    if (prioritySelect) prioritySelect.value = 'medium';
    if (subjectSelect) subjectSelect.value = currentFilters.subject_id || '';
  }

  if (modal) {
    modal.classList.add('show');
    if (titleInput) titleInput.focus();
  }
};

window.closeTaskModal = function () {
  const modal = document.getElementById('task-modal');
  if (modal) modal.classList.remove('show');
  editingTaskId = null;
};

/**
 * Setup Task Form submit
 */
function setupForm() {
  const form = document.getElementById('task-form');
  if (!form) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const submitBtn = form.querySelector('button[type="submit"]');
    const titleInput = document.getElementById('task-title-input');
    const descInput = document.getElementById('task-description');
    const dueDateInput = document.getElementById('task-due-date');
    const prioritySelect = document.getElementById('task-priority');
    const subjectSelect = document.getElementById('task-subject');

    const title = titleInput ? titleInput.value.trim() : '';
    const description = descInput ? descInput.value.trim() : '';
    const dueDateVal = dueDateInput ? dueDateInput.value : '';
    const priority = prioritySelect ? prioritySelect.value : 'medium';
    const subjectIdVal = subjectSelect ? subjectSelect.value : '';

    if (!title) {
      showToast('Por favor escribe un título para la tarea', 'error');
      return;
    }

    let due_date = null;
    if (dueDateVal) {
      due_date = new Date(dueDateVal + 'T23:59:59').toISOString();
    }

    const payload = {
      title,
      description,
      priority,
      due_date,
      subject_id: subjectIdVal ? parseInt(subjectIdVal, 10) : null
    };

    setLoading(submitBtn, true);

    try {
      let res;
      if (editingTaskId !== null) {
        res = await apiRequest('PUT', `/tasks/${editingTaskId}`, payload);
      } else {
        payload.status = 'pending';
        res = await apiRequest('POST', '/tasks/', payload);
      }

      if (res.ok) {
        showToast(editingTaskId !== null ? 'Tarea actualizada' : 'Tarea creada exitosamente');
        closeTaskModal();
        await loadTasks();
      } else {
        const err = await res.json().catch(() => ({}));
        showToast(err.detail || 'Error al guardar la tarea', 'error');
      }
    } catch (err) {
      console.error('Error saving task:', err);
      showToast('Error de red al guardar tarea', 'error');
    } finally {
      setLoading(submitBtn, false);
    }
  });
}

/**
 * Delete a task
 */
window.deleteTask = async function (id) {
  if (!confirm('¿Estás seguro de que deseas eliminar esta tarea?')) {
    return;
  }

  try {
    const res = await apiRequest('DELETE', `/tasks/${id}`);
    if (res.ok) {
      showToast('Tarea eliminada exitosamente');
      await loadTasks();
    } else {
      const err = await res.json().catch(() => ({}));
      showToast(err.detail || 'No fue posible eliminar la tarea', 'error');
    }
  } catch (err) {
    console.error('Error deleting task:', err);
    showToast('Error de conexión', 'error');
  }
};

/**
 * Helper to display human-readable status labels
 */
function getStatusLabel(status) {
  switch (status) {
    case 'done': return 'Completada';
    case 'in_progress': return 'En progreso';
    case 'pending': return 'Pendiente';
    default: return status || 'Pendiente';
  }
}

/**
 * Helper to display human-readable priority labels
 */
function getPriorityLabel(priority) {
  switch (priority) {
    case 'high': return 'Alta';
    case 'medium': return 'Media';
    case 'low': return 'Baja';
    default: return priority || 'Media';
  }
}

/**
 * Button loading state
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
