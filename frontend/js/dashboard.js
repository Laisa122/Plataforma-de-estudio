/**
 * StudySync - Dashboard Management & Metrics
 */

document.addEventListener('DOMContentLoaded', () => {
  requireAuth();
  loadUserInfo();
  setupLogout();
  loadDashboardData();
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
 * Fetches dashboard data concurrently
 */
async function loadDashboardData() {
  try {
    const [subjectsRes, tasksRes, groupsRes] = await Promise.all([
      apiRequest('GET', '/subjects/'),
      apiRequest('GET', '/tasks/'),
      apiRequest('GET', '/groups/')
    ]);

    const subjects = subjectsRes.ok ? await subjectsRes.json() : [];
    const tasks = tasksRes.ok ? await tasksRes.json() : [];
    const groups = groupsRes.ok ? await groupsRes.json() : [];

    renderStats(subjects, tasks, groups);
    renderUpcomingTasks(tasks, subjects);
    renderRecentSubjects(subjects);
  } catch (error) {
    console.error('Error loading dashboard data:', error);
    showToast('Error al cargar la información del panel', 'error');
  }
}

/**
 * Renders summary metrics in stat cards
 */
function renderStats(subjects = [], tasks = [], groups = []) {
  const statSubjects = document.getElementById('stat-subjects');
  const statPending = document.getElementById('stat-pending');
  const statOverdue = document.getElementById('stat-overdue');
  const statGroups = document.getElementById('stat-groups');

  const pendingCount = tasks.filter(t => t.status === 'pending' || t.status === 'in_progress').length;
  const overdueCount = tasks.filter(t => t.status !== 'done' && isOverdue(t.due_date)).length;

  if (statSubjects) statSubjects.textContent = subjects.length;
  if (statPending) statPending.textContent = pendingCount;
  if (statOverdue) statOverdue.textContent = overdueCount;
  if (statGroups) statGroups.textContent = groups.length;
}

/**
 * Renders up to 5 upcoming pending tasks sorted by due date
 */
function renderUpcomingTasks(tasks = [], subjects = []) {
  const container = document.getElementById('upcoming-tasks');
  if (!container) return;

  const subjectMap = {};
  subjects.forEach(s => {
    subjectMap[s.id] = s;
  });

  const pendingWithDue = tasks
    .filter(t => t.status !== 'done' && t.due_date)
    .sort((a, b) => new Date(a.due_date).getTime() - new Date(b.due_date).getTime())
    .slice(0, 5);

  if (pendingWithDue.length === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <div class="empty-state-icon">🎉</div>
        <div class="empty-state-title">Todo al día</div>
        <div class="empty-state-desc">No tienes tareas pendientes con fechas próximas. ¡Buen trabajo!</div>
      </div>
    `;
    return;
  }

  container.innerHTML = `
    <div class="tasks-list">
      ${pendingWithDue.map(task => {
        const overdue = isOverdue(task.due_date);
        const subj = subjectMap[task.subject_id];
        const statusClass = task.status === 'done' ? 'done' : task.status === 'in_progress' ? 'in_progress' : 'pending';
        return `
          <div class="task-item" id="task-${task.id}">
            <div class="task-checkbox ${statusClass}" title="Estado: ${task.status}">
              ${task.status === 'done' ? '✓' : ''}
            </div>
            <div class="task-content">
              <span class="task-title">${escapeHtml(task.title)}</span>
              <div class="task-meta">
                ${subj ? `<span class="badge badge-subject" style="border-left: 3px solid ${subj.color || '#6366f1'}">${escapeHtml(subj.name)}</span>` : ''}
                <span class="badge badge-${task.priority || 'medium'}">${task.priority || 'media'}</span>
                <span class="due-date ${overdue ? 'overdue' : ''}">
                  📅 ${formatDate(task.due_date)} ${overdue ? '(Vencida)' : ''}
                </span>
              </div>
            </div>
          </div>
        `;
      }).join('')}
    </div>
  `;
}

/**
 * Renders up to 4 recent subjects
 */
function renderRecentSubjects(subjects = []) {
  const container = document.getElementById('recent-subjects');
  if (!container) return;

  const recent = subjects.slice(0, 4);

  if (recent.length === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <div class="empty-state-icon">📚</div>
        <div class="empty-state-title">Sin materias registradas</div>
        <div class="empty-state-desc">Aún no has agregado materias a tu semestre.</div>
        <a href="/subjects" class="btn btn-outline btn-sm" style="margin-top: 1rem;">+ Agregar Materia</a>
      </div>
    `;
    return;
  }

  container.innerHTML = `
    <div style="display: flex; flex-direction: column; gap: 0.85rem;">
      ${recent.map(subj => {
        const color = subj.color || '#6366f1';
        return `
          <div style="background: rgba(15, 23, 42, 0.45); border: 1px solid var(--border-color); border-left: 4px solid ${color}; border-radius: 10px; padding: 0.9rem 1.1rem; display: flex; align-items: center; justify-content: space-between;">
            <div>
              <div style="font-weight: 600; color: var(--text-primary); font-size: 0.95rem;">${escapeHtml(subj.name)}</div>
              <div style="font-size: 0.8rem; color: var(--text-muted); margin-top: 2px;">
                ${subj.professor ? `👨‍🏫 ${escapeHtml(subj.professor)}` : ''} 
                ${subj.semester ? ` • 📅 ${escapeHtml(subj.semester)}` : ''}
              </div>
            </div>
            <a href="/tasks" class="btn btn-icon btn-sm" title="Ver tareas">
              ➜
            </a>
          </div>
        `;
      }).join('')}
    </div>
  `;
}
