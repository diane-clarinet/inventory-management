<!--
  Starting point for the app-shell sidebar. Adapt to the app:
  - replace `links` with the app's real routes and i18n keys
  - keep shell features (language switcher, profile menu) in the footer slot
  - styles use tokens from references/design-tokens.md
-->
<template>
  <div class="shell">
    <header class="mobile-bar">
      <button class="hamburger" aria-label="Open navigation" @click="open = true">
        <svg viewBox="0 0 20 20" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 5h14M3 10h14M3 15h14" /></svg>
      </button>
      <span class="brand-name">{{ brand }}</span>
    </header>

    <div v-if="open" class="scrim" @click="open = false" />

    <aside class="sidebar" :class="{ open }">
      <div class="brand confetti">
        <span class="brand-name">{{ brand }}</span>
        <span class="eyebrow">{{ tagline }}</span>
      </div>

      <nav aria-label="Primary" class="nav">
        <router-link
          v-for="link in links"
          :key="link.to"
          :to="link.to"
          class="nav-link"
          :aria-current="isActive(link.to) ? 'page' : undefined"
          :class="{ active: isActive(link.to) }"
          @click="open = false"
        >
          <svg class="icon" viewBox="0 0 20 20" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <path :d="link.icon" />
          </svg>
          <span>{{ link.label }}</span>
        </router-link>
      </nav>

      <div class="zigzag" />
      <div class="sidebar-footer">
        <slot name="footer" />
      </div>
    </aside>

    <main class="content">
      <slot />
    </main>
  </div>
</template>

<script>
import { ref, watch } from 'vue'
import { useRoute } from 'vue-router'

export default {
  name: 'AppSidebar',
  props: {
    brand: { type: String, required: true },
    tagline: { type: String, default: '' },
    // [{ to: '/', label: 'Overview', icon: '<svg path d>' }]
    links: { type: Array, required: true }
  },
  setup() {
    const route = useRoute()
    const open = ref(false)
    const isActive = (to) => (to === '/' ? route.path === '/' : route.path.startsWith(to))
    watch(() => route.path, () => { open.value = false })
    return { open, isActive }
  }
}

/* Example 20x20 icon paths (stroke style) to pass in `links`:
   overview:  'M3 10l7-7 7 7M5 8v8h10V8'
   inventory: 'M3 6l7-3 7 3-7 3-7-3zM3 6v8l7 3 7-3V6'
   orders:    'M5 3h10v14H5zM8 7h4M8 11h4'
   finance:   'M10 3v14M13 6.5C13 5.5 11.8 5 10 5S7 5.7 7 7s1.5 1.8 3 2 3 .7 3 2-1.2 2-3 2-3-.6-3-1.6'
   demand:    'M3 16l4-5 3 3 6-8'
   restock:   'M4 10a6 6 0 0110-4l2 2M16 10a6 6 0 01-10 4l-2-2M16 4v4h-4M4 16v-4h4'
   reports:   'M4 17V9M10 17V3M16 17v-6'
*/
</script>

<style scoped>
.shell { min-height: 100vh; background: var(--paper); }

.sidebar {
  position: fixed; inset: 0 auto 0 0; width: var(--sidebar-width);
  background: var(--ink-900); color: #fff;
  display: flex; flex-direction: column; gap: var(--space-4);
  padding: var(--space-5) var(--space-4); z-index: 40;
  border-right: var(--border-pop);
}
.brand { padding: var(--space-4); border-radius: var(--radius-md); border: 2px solid var(--teal-500); display: grid; gap: var(--space-1); }
.brand-name { font-family: var(--font-display); font-weight: 800; font-size: var(--text-lg); }
.brand .eyebrow { color: var(--yellow-400); }

.nav { display: grid; gap: var(--space-2); flex: 1; align-content: start; }
.nav-link {
  display: flex; align-items: center; gap: var(--space-3);
  padding: var(--space-3) var(--space-4); border-radius: var(--radius-sm);
  color: #cbd5e1; text-decoration: none; font-weight: 600; font-size: var(--text-sm);
  border: 2px solid transparent; transition: transform .08s, box-shadow .08s;
}
.nav-link:hover { color: #fff; border-color: var(--ink-700); }
.nav-link.active {
  background: var(--teal-500); color: var(--ink-900); border-color: #fff;
  box-shadow: 3px 3px 0 var(--pink-500);
}
.sidebar-footer { display: grid; gap: var(--space-3); }

.content { margin-left: var(--sidebar-width); padding: var(--space-5); max-width: calc(1280px + var(--sidebar-width)); }

.mobile-bar { display: none; }
.scrim { position: fixed; inset: 0; background: rgb(15 23 42 / 0.6); z-index: 30; }
.hamburger { background: transparent; border: var(--border-pop); border-radius: var(--radius-sm); padding: var(--space-2); color: inherit; cursor: pointer; }

@media (max-width: 900px) {
  .mobile-bar {
    display: flex; align-items: center; gap: var(--space-3);
    position: sticky; top: 0; z-index: 20; padding: var(--space-3) var(--space-4);
    background: var(--ink-900); color: #fff;
  }
  .sidebar { transform: translateX(-100%); transition: transform .2s; }
  .sidebar.open { transform: none; }
  .content { margin-left: 0; padding: var(--space-4); }
}
</style>
