import { createRouter, createWebHistory } from "vue-router";
import Home from "../views/Home.vue";
import Hot100 from "../views/Hot100.vue";

const routes = [
  {
    path: "/",
    name: "Home",
    component: Home,
    meta: { label: "Home", icon: "pi pi-home" },
  },
  {
    path: "/hot-100",
    name: "Hot100",
    component: Hot100,
    meta: { label: "Hot 100", icon: "pi pi-chart-line" },
  },
  //   {
  //     path: "/about",
  //     name: "About",
  //     component: () => import("../views/About.vue"), // Lazy-loaded route
  //     meta: { label: "About", icon: "pi pi-info-circle" },
  //   },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;
