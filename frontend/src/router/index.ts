import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      component: () => import('@/components/Layout.vue'),
      redirect: '/dashboard',
      children: [
        {
          path: 'dashboard',
          name: 'Dashboard',
          component: () => import('@/views/Dashboard.vue'),
          meta: { title: '仪表盘' },
        },
        {
          path: 'manufacturers',
          name: 'Manufacturers',
          component: () => import('@/views/Manufacturers.vue'),
          meta: { title: '厂商管理' },
        },
        {
          path: 'filaments',
          name: 'Filaments',
          component: () => import('@/views/Filaments.vue'),
          meta: { title: '耗材管理' },
        },
        {
          path: 'spools',
          name: 'Spools',
          component: () => import('@/views/Spools.vue'),
          meta: { title: '料盘管理' },
        },
        {
          path: 'print-records',
          name: 'PrintRecords',
          component: () => import('@/views/PrintRecords.vue'),
          meta: { title: '打印记录' },
        },
        {
          path: 'printers',
          name: 'PrinterConfig',
          component: () => import('@/views/PrinterConfig.vue'),
          meta: { title: '打印机配置' },
        },
        {
          path: 'mqtt-messages',
          name: 'MqttMessages',
          component: () => import('@/views/MqttMessages.vue'),
          meta: { title: '消息列表' },
        },
        {
          path: 'operation-logs',
          name: 'OperationLogs',
          component: () => import('@/views/OperationLogs.vue'),
          meta: { title: '操作日志' },
        },
      ],
    },
  ],
})

export default router
