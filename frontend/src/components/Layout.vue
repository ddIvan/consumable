<template>
  <el-container class="app-container">
    <el-aside width="220px" class="app-aside">
      <div class="logo">
        <el-icon :size="24"><Coin /></el-icon>
        <span>耗材管理器</span>
      </div>
      <el-menu
        :default-active="route.path"
        router
        background-color="#1d1e1f"
        text-color="#bfcbd9"
        active-text-color="#409eff"
      >
        <el-menu-item index="/dashboard">
          <el-icon><Odometer /></el-icon>
          <span>仪表盘</span>
        </el-menu-item>
        <el-menu-item index="/manufacturers">
          <el-icon><Shop /></el-icon>
          <span>厂商管理</span>
        </el-menu-item>
        <el-menu-item index="/filaments">
          <el-icon><List /></el-icon>
          <span>耗材管理</span>
        </el-menu-item>
        <el-menu-item index="/spools">
          <el-icon><Coin /></el-icon>
          <span>料盘管理</span>
        </el-menu-item>
        <el-menu-item index="/print-records">
          <el-icon><Document /></el-icon>
          <span>打印记录</span>
        </el-menu-item>
        <el-menu-item index="/printers">
          <el-icon><Monitor /></el-icon>
          <span>打印机</span>
        </el-menu-item>
        <el-menu-item index="/mqtt-messages">
          <el-icon><Message /></el-icon>
          <span>消息列表</span>
        </el-menu-item>
        <el-menu-item index="/operation-logs">
          <el-icon><Tickets /></el-icon>
          <span>操作日志</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-container class="app-right">
      <el-header class="app-header">
        <h2>{{ route.meta.title }}</h2>
        <div class="header-right">
          <printer-status-badge v-if="printerConnected" />
        </div>
      </el-header>
      <el-main class="app-main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import PrinterStatusBadge from './PrinterStatusBadge.vue'

const route = useRoute()
const printerConnected = ref(false)

let ws: WebSocket | null = null

onMounted(() => {
  // Try to find first printer and connect via WebSocket
  import('@/api').then(({ printerApi }) => {
    printerApi.list().then((res) => {
      const printers = res.data
      if (printers.length > 0) {
        connectWs(printers[0].id)
      }
    })
  })
})

onUnmounted(() => {
  ws?.close()
})

function connectWs(printerId: number) {
  const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:'
  ws = new WebSocket(`${protocol}//${location.host}/ws/printer/${printerId}`)
  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      if (data.type === 'connection') {
        printerConnected.value = data.connected
      }
    } catch {}
  }
  ws.onclose = () => {
    printerConnected.value = false
  }
}
</script>

<style>
/* Global: eliminate body scrollbar */
html, body, #app {
  margin: 0;
  padding: 0;
  height: 100%;
  overflow: hidden;
}
</style>

<style scoped>
.app-container {
  height: 100vh;
  overflow: hidden;
}
.app-right {
  overflow: hidden;
}
.app-aside {
  background-color: #1d1e1f;
  overflow-y: auto;
}
.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 18px;
  font-weight: 600;
  gap: 8px;
  border-bottom: 1px solid #333;
}
.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
  padding: 0 20px;
  height: 60px;
}
.app-header h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}
.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}
.app-main {
  background: #f5f7fa;
  padding: 20px;
  overflow-y: auto;
}
</style>
