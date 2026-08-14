import { createRouter, createWebHistory } from "vue-router"
import { useAuthStore } from "@/stores/auth"

const routes = [
  // Root redirect
  { path: "/", component: () => import("@/pages/index.vue") },

  // Auth pages (no sidebar)
  {
    path: "/auth",
    component: () => import("@/components/AuthLayout.vue"),
    children: [
      { path: "login",    name: "login",    component: () => import("@/pages/auth/login.vue") },
      { path: "register", name: "register", component: () => import("@/pages/auth/register.vue") },
    ],
  },

  // App pages (with sidebar)
  {
    path: "/",
    component: () => import("@/components/AppLayout.vue"),
    meta: { requiresAuth: true },
    children: [
      { path: "home",       name: "home",       component: () => import("@/pages/home.vue") },
      { path: "datasets",   name: "datasets",   component: () => import("@/pages/datasets/index.vue") },
      { path: "datasets/:id", name: "dataset-detail", component: () => import("@/pages/datasets/detail.vue") },
      { path: "chat",       name: "chat",       component: () => import("@/pages/chat/index.vue") },
      { path: "chat/:id",   name: "chat-detail", component: () => import("@/pages/chat/session.vue") },
      { path: "dashboards", name: "dashboards", component: () => import("@/pages/dashboards/index.vue") },
      { path: "dashboards/:id", name: "dashboard-detail", component: () => import("@/pages/dashboards/detail.vue") },
      { path: "profile",    name: "profile",    component: () => import("@/pages/profile.vue") },
    ],
  },

  // Catch-all
  { path: "/:pathMatch(.*)*", redirect: "/" },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior: () => ({ top: 0 }),
})

// Auth guard
router.beforeEach((to) => {
  const auth = useAuthStore()
  if (to.meta.requiresAuth && !auth.isLoggedIn) {
    return { name: "login" }
  }
  if ((to.name === "login" || to.name === "register") && auth.isLoggedIn) {
    return { name: "home" }
  }
})

export default router
