import { createApp } from "vue";
import { createPinia } from "pinia";

import App from "./App.vue";
import "./style.css";
import PrimeVue from "primevue/config";
import Aura from "@primevue/themes/aura";
import "primeicons/primeicons.css";

const app = createApp(App);

app.use(createPinia());

app.use(PrimeVue, {
  theme: {
    preset: Aura,
  },
});

app.mount("#app");
