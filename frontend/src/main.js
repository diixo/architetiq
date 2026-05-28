import { createApp } from 'vue'
import { createPinia } from 'pinia'
import 'bootstrap/dist/css/bootstrap.min.css'
import 'bootstrap-icons/font/bootstrap-icons.css'
import 'bootstrap/dist/js/bootstrap.bundle.min.js'
import '@mdi/font/css/materialdesignicons.min.css'
import '@fortawesome/fontawesome-free/css/all.min.css'
import 'icofont/dist/icofont.min.css'
import 'material-icons/iconfont/material-icons.css'
import './architetiq.css'
import './style.css'
import App from './App.vue'

createApp(App).use(createPinia()).mount('#app')
