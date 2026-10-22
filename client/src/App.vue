<template>
  <div class="app">
    <header class="mobile-bar">
      <button class="hamburger" aria-label="Open navigation" @click="navOpen = true">
        <svg viewBox="0 0 20 20" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 5h14M3 10h14M3 15h14" /></svg>
      </button>
      <span class="brand-name">{{ t('nav.companyName') }}</span>
    </header>

    <div v-if="navOpen" class="scrim" @click="navOpen = false"></div>

    <aside class="sidebar" :class="{ open: navOpen }">
      <div class="brand confetti-wrap">
        <span class="brand-name">{{ t('nav.companyName') }}</span>
        <span class="eyebrow">{{ t('nav.subtitle') }}</span>
        <svg class="brand-shapes" viewBox="0 0 64 64" width="64" height="64" aria-hidden="true">
          <polygon points="6,34 22,34 14,18" fill="#ffd60a" />
          <path d="M26 50 q4 -8 8 0 t8 0 t8 0" fill="none" stroke="#ff3d9a" stroke-width="3" stroke-linecap="round" />
          <circle cx="50" cy="20" r="5" fill="none" stroke="#00d4bd" stroke-width="3" />
        </svg>
      </div>

      <nav aria-label="Primary" class="nav">
        <router-link
          v-for="link in links"
          :key="link.to"
          :to="link.to"
          class="nav-link"
          :class="{ active: isActive(link.to) }"
          :aria-current="isActive(link.to) ? 'page' : undefined"
        >
          <svg class="icon" viewBox="0 0 20 20" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <path :d="link.icon" />
          </svg>
          <span>{{ link.label }}</span>
        </router-link>
      </nav>

      <div class="zigzag"></div>
      <div class="sidebar-footer">
        <LanguageSwitcher />
        <ProfileMenu
          @show-profile-details="showProfileDetails = true"
          @show-tasks="showTasks = true"
        />
      </div>
    </aside>

    <div class="content">
      <FilterBar />
      <main class="main-content">
        <router-view />
      </main>
    </div>

    <ProfileDetailsModal
      :is-open="showProfileDetails"
      @close="showProfileDetails = false"
    />

    <TasksModal
      :is-open="showTasks"
      :tasks="tasks"
      @close="showTasks = false"
      @add-task="addTask"
      @delete-task="deleteTask"
      @toggle-task="toggleTask"
    />
  </div>
</template>

<script>
import { ref, onMounted, computed, watch } from 'vue'
import { useRoute } from 'vue-router'
import { api } from './api'
import { useAuth } from './composables/useAuth'
import { useI18n } from './composables/useI18n'
import FilterBar from './components/FilterBar.vue'
import ProfileMenu from './components/ProfileMenu.vue'
import ProfileDetailsModal from './components/ProfileDetailsModal.vue'
import TasksModal from './components/TasksModal.vue'
import LanguageSwitcher from './components/LanguageSwitcher.vue'

export default {
  name: 'App',
  components: {
    FilterBar,
    ProfileMenu,
    ProfileDetailsModal,
    TasksModal,
    LanguageSwitcher
  },
  setup() {
    const { currentUser } = useAuth()
    const { t } = useI18n()
    const route = useRoute()
    const navOpen = ref(false)
    const links = computed(() => [
      { to: '/', label: t('nav.overview'), icon: 'M3 10l7-7 7 7M5 8v8h10V8' },
      { to: '/inventory', label: t('nav.inventory'), icon: 'M3 6l7-3 7 3-7 3-7-3zM3 6v8l7 3 7-3V6' },
      { to: '/orders', label: t('nav.orders'), icon: 'M5 3h10v14H5zM8 7h4M8 11h4' },
      { to: '/spending', label: t('nav.finance'), icon: 'M10 3v14M13 6.5C13 5.5 11.8 5 10 5S7 5.7 7 7s1.5 1.8 3 2 3 .7 3 2-1.2 2-3 2-3-.6-3-1.6' },
      { to: '/demand', label: t('nav.demandForecast'), icon: 'M3 16l4-5 3 3 6-8' },
      { to: '/restocking', label: t('nav.restocking'), icon: 'M4 10a6 6 0 0110-4l2 2M16 10a6 6 0 01-10 4l-2-2M16 4v4h-4M4 16v-4h4' },
      { to: '/reports', label: 'Reports', icon: 'M4 17V9M10 17V3M16 17v-6' }
    ])
    const isActive = (to) => (to === '/' ? route.path === '/' : route.path.startsWith(to))
    watch(() => route.path, () => { navOpen.value = false })
    const showProfileDetails = ref(false)
    const showTasks = ref(false)
    const apiTasks = ref([])

    // Merge mock tasks from currentUser with API tasks
    const tasks = computed(() => {
      return [...currentUser.value.tasks, ...apiTasks.value]
    })

    const loadTasks = async () => {
      try {
        apiTasks.value = await api.getTasks()
      } catch (err) {
        console.error('Failed to load tasks:', err)
      }
    }

    const addTask = async (taskData) => {
      try {
        const newTask = await api.createTask(taskData)
        // Add new task to the beginning of the array
        apiTasks.value.unshift(newTask)
      } catch (err) {
        console.error('Failed to add task:', err)
      }
    }

    const deleteTask = async (taskId) => {
      try {
        // Check if it's a mock task (from currentUser)
        const isMockTask = currentUser.value.tasks.some(t => t.id === taskId)

        if (isMockTask) {
          // Remove from mock tasks
          const index = currentUser.value.tasks.findIndex(t => t.id === taskId)
          if (index !== -1) {
            currentUser.value.tasks.splice(index, 1)
          }
        } else {
          // Remove from API tasks
          await api.deleteTask(taskId)
          apiTasks.value = apiTasks.value.filter(t => t.id !== taskId)
        }
      } catch (err) {
        console.error('Failed to delete task:', err)
      }
    }

    const toggleTask = async (taskId) => {
      try {
        // Check if it's a mock task (from currentUser)
        const mockTask = currentUser.value.tasks.find(t => t.id === taskId)

        if (mockTask) {
          // Toggle mock task status
          mockTask.status = mockTask.status === 'pending' ? 'completed' : 'pending'
        } else {
          // Toggle API task
          const updatedTask = await api.toggleTask(taskId)
          const index = apiTasks.value.findIndex(t => t.id === taskId)
          if (index !== -1) {
            apiTasks.value[index] = updatedTask
          }
        }
      } catch (err) {
        console.error('Failed to toggle task:', err)
      }
    }

    onMounted(loadTasks)

    return {
      t,
      navOpen,
      links,
      isActive,
      showProfileDetails,
      showTasks,
      tasks,
      addTask,
      deleteTask,
      toggleTask
    }
  }
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: var(--font-body);
  background: var(--paper);
  color: var(--ink-900);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

.app {
  min-height: 100vh;
}

/* Sidebar */
.sidebar {
  position: fixed;
  inset: 0 auto 0 0;
  width: var(--sidebar-width);
  background:
    repeating-linear-gradient(135deg, rgb(255 255 255 / 0.04) 0 2px, transparent 2px 14px),
    var(--ink-900);
  color: #fff;
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  padding: var(--space-5) var(--space-4);
  z-index: 40;
}

.brand {
  position: relative;
  overflow: hidden;
  padding: var(--space-4);
  border-radius: var(--radius-md);
  border: 2px solid var(--teal-500);
  display: grid;
  gap: var(--space-1);
}

.brand::after {
  content: '';
  position: absolute;
  inset: 0 0 0 auto;
  width: 64px;
  opacity: 0.8;
  pointer-events: none;
  background-image:
    radial-gradient(var(--yellow-400) 3px, transparent 3.5px),
    radial-gradient(var(--pink-500) 2px, transparent 2.5px);
  background-size: 28px 28px, 44px 44px;
  background-position: 0 0, 14px 18px;
}

.brand-shapes {
  position: absolute;
  right: 4px;
  bottom: 2px;
  opacity: 0.9;
  pointer-events: none;
}

.brand-name {
  font-family: var(--font-display);
  font-weight: 800;
  font-size: var(--text-lg);
  letter-spacing: -0.01em;
}

.brand .eyebrow {
  color: var(--yellow-400);
}

.nav {
  display: grid;
  gap: var(--space-2);
  flex: 1;
  align-content: start;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-sm);
  color: var(--ink-300);
  text-decoration: none;
  font-weight: 600;
  font-size: var(--text-sm);
  border: 2px solid transparent;
  position: relative;
  transition: transform 0.12s, box-shadow 0.08s;
}

.nav-link::before {
  content: '';
  position: absolute;
  left: -2px;
  top: 4px;
  bottom: 4px;
  width: 4px;
  border-radius: 2px;
  background: var(--yellow-400);
  opacity: 0;
  transition: opacity 0.12s;
}

.nav-link:hover {
  color: #fff;
  border-color: var(--ink-700);
  transform: translateX(3px);
}

.nav-link:hover::before {
  opacity: 1;
}

.nav-link.active {
  background: var(--teal-500);
  color: var(--ink-900);
  border-color: #fff;
  box-shadow: 4px 4px 0 var(--pink-500), 7px 7px 0 var(--purple-500);
}

.nav-link.active::before {
  display: none;
}

.sidebar-footer {
  display: grid;
  gap: var(--space-3);
}

.sidebar-footer > * {
  min-width: 0;
}

.content {
  margin-left: var(--sidebar-width);
  min-height: 100vh;
}

.main-content {
  min-width: 0;
  max-width: 1280px;
  width: 100%;
  margin: 0 auto;
  padding: var(--space-5);
}

.mobile-bar {
  display: none;
}

.scrim {
  position: fixed;
  inset: 0;
  background: rgb(15 23 42 / 0.6);
  z-index: 30;
}

.hamburger {
  background: transparent;
  border: 2px solid #fff;
  border-radius: var(--radius-sm);
  padding: var(--space-2);
  color: inherit;
  cursor: pointer;
  display: flex;
}

@media (max-width: 900px) {
  .mobile-bar {
    display: flex;
    align-items: center;
    gap: var(--space-3);
    position: sticky;
    top: 0;
    z-index: 50;
    height: var(--topbar-height);
    padding: 0 var(--space-4);
    background: var(--ink-900);
    color: #fff;
  }
  .sidebar {
    padding-top: calc(var(--topbar-height) + var(--space-4));
    transform: translateX(-100%);
    transition: transform 0.2s;
  }
  .sidebar.open {
    transform: none;
  }
  .content {
    margin-left: 0;
    min-height: 0;
  }
  .main-content :is(.card, .chart-card) {
    min-width: 0;
    overflow-x: auto;
  }
  .main-content {
    padding: var(--space-4);
  }
}

@media (prefers-reduced-motion: reduce) {
  .nav-link, .nav-link::before, .stat-card, .sidebar { transition: none; }
  .nav-link:hover { transform: none; }
}

/* Shared page patterns */
.page-header {
  position: relative;
  margin-bottom: var(--space-5);
  padding-bottom: var(--space-4);
}

.page-header::after {
  content: '';
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  height: 10px;
  background:
    linear-gradient(135deg, var(--pink-500) 25%, transparent 25%) -10px 0,
    linear-gradient(225deg, var(--pink-500) 25%, transparent 25%) -10px 0;
  background-size: 20px 20px;
  pointer-events: none;
}

.page-header h2 {
  position: relative;
  z-index: 0;
  display: inline-block;
  padding-left: var(--space-3);
}

.page-header h2::before {
  content: '';
  position: absolute;
  z-index: -1;
  left: 0;
  top: 18%;
  bottom: -2px;
  width: 56%;
  background: var(--teal-500);
  transform: skewX(-18deg);
  opacity: 0.55;
}

.page-header h2 {
  font-size: var(--text-xl);
  font-weight: 800;
  color: var(--ink-900);
  margin-bottom: var(--space-2);
}

.page-header p {
  color: var(--ink-500);
  font-size: var(--text-sm);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: var(--space-5);
  margin-bottom: var(--space-5);
}

.stat-card {
  background: var(--surface);
  padding: var(--space-5);
  border-radius: var(--radius-md);
  border: var(--border-pop);
  box-shadow: var(--shadow-pop);
  transition: transform 0.08s, box-shadow 0.08s;
}

/* Accent top stripe (absolute: no layout change) */
.stat-card,
.card {
  position: relative;
  --stripe: var(--teal-500);
}

.stat-card::before,
.card::before {
  content: '';
  position: absolute;
  top: -2px;
  left: -2px;
  right: -2px;
  height: 5px;
  border-radius: var(--radius-md) var(--radius-md) 0 0;
  background: var(--stripe);
  border-bottom: 2px solid var(--ink-900);
  pointer-events: none;
}

.stat-card:nth-child(4n+2), .card:nth-child(4n+2) { --stripe: var(--purple-500); }
.stat-card:nth-child(4n+3), .card:nth-child(4n+3) { --stripe: var(--pink-500); }
.stat-card:nth-child(4n+4), .card:nth-child(4n+4) { --stripe: var(--yellow-400); }

.stat-card:hover {
  transform: translate(-1px, -1px);
  box-shadow: 6px 6px 0 var(--ink-900);
}

.stat-label {
  color: var(--ink-500);
  font-size: var(--text-xs);
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  margin-bottom: var(--space-2);
}

.stat-value {
  font-family: var(--font-display);
  font-size: var(--text-xl);
  font-weight: 800;
  color: var(--ink-900);
  letter-spacing: -0.01em;
}

.stat-card.warning .stat-value { color: var(--warning-ink); }
.stat-card.success .stat-value { color: var(--success); }
.stat-card.danger .stat-value { color: var(--danger); }
.stat-card.info .stat-value { color: var(--info); }

.card {
  background: var(--surface);
  border-radius: var(--radius-md);
  padding: var(--space-5);
  border: var(--border-pop);
  box-shadow: var(--shadow-pop);
  margin-bottom: var(--space-5);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-4);
  padding-bottom: var(--space-3);
  border-bottom: 2px solid var(--ink-900);
}

.card-title {
  font-family: var(--font-display);
  font-size: var(--text-md);
  font-weight: 800;
  color: var(--ink-900);
}

.table-container {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
}

thead {
  background: var(--paper);
  border-bottom: 2px solid var(--ink-900);
}

th {
  text-align: left;
  padding: var(--space-3);
  font-weight: 700;
  color: var(--ink-600);
  font-size: var(--text-xs);
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

td {
  padding: var(--space-3);
  border-top: var(--border-soft);
  color: var(--ink-700);
  font-size: var(--text-sm);
}

tbody tr {
  transition: background-color 0.15s ease;
}

tbody tr:hover {
  background: var(--teal-100);
}

.badge {
  display: inline-block;
  padding: 2px var(--space-2);
  border-radius: 999px;
  font-size: var(--text-xs);
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  border: 1px solid currentColor;
}

.badge.success, .badge.increasing { background: var(--success-bg); color: var(--success-ink); }
.badge.warning, .badge.medium { background: var(--warning-bg); color: var(--warning-ink); }
.badge.danger, .badge.decreasing, .badge.high { background: var(--danger-bg); color: var(--danger-ink); }
.badge.info, .badge.low { background: var(--info-bg); color: var(--info-ink); }
.badge.stable { background: var(--purple-100); color: #5b21b6; }

.loading {
  text-align: center;
  padding: var(--space-7);
  color: var(--ink-500);
  font-size: var(--text-sm);
}

.error {
  background: var(--danger-bg);
  border: 1px solid #fecaca;
  color: var(--danger-ink);
  padding: var(--space-4);
  border-radius: var(--radius-md);
  margin: var(--space-4) 0;
  font-size: var(--text-sm);
}
</style>
