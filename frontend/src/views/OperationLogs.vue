<template>
  <div>
    <div class="page-header">
      <el-select v-model="levelFilter" placeholder="日志级别" clearable style="width: 120px" @change="load">
        <el-option label="全部" value="" />
        <el-option label="信息" value="info" />
        <el-option label="警告" value="warning" />
        <el-option label="错误" value="error" />
      </el-select>
      <el-button type="danger" :disabled="!list.length" @click="handleClear">清空日志</el-button>
    </div>

    <el-table :data="list" stripe v-loading="loading">
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="created_at" label="时间" width="170">
        <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
      </el-table-column>
      <el-table-column prop="level" label="级别" width="80">
        <template #default="{ row }">
          <el-tag :type="levelType(row.level)" size="small">{{ levelLabel(row.level) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="action" label="操作" width="140">
        <template #default="{ row }">{{ actionLabel(row.action) }}</template>
      </el-table-column>
      <el-table-column prop="target" label="对象" width="160" show-overflow-tooltip />
      <el-table-column prop="message" label="消息" min-width="300" show-overflow-tooltip />
    </el-table>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { operationLogApi } from '@/api'
import { ElMessage, ElMessageBox } from 'element-plus'

const list = ref<any[]>([])
const loading = ref(false)
const levelFilter = ref('')

onMounted(() => load())

async function load() {
  loading.value = true
  try {
    const params: any = { limit: 200 }
    if (levelFilter.value) params.level = levelFilter.value
    const res = await operationLogApi.list(params)
    list.value = res.data
  } finally {
    loading.value = false
  }
}

async function handleClear() {
  try {
    await ElMessageBox.confirm('确定清空所有操作日志？', '确认', { type: 'warning' })
    await operationLogApi.clear()
    ElMessage.success('已清空')
    await load()
  } catch {}
}

function levelType(level: string) {
  if (level === 'error') return 'danger'
  if (level === 'warning') return 'warning'
  return 'info'
}

function levelLabel(level: string) {
  if (level === 'error') return '错误'
  if (level === 'warning') return '警告'
  return '信息'
}

function actionLabel(action: string) {
  const labels: Record<string, string> = {
    printer_connect: '打印机连接',
  }
  return labels[action] || action
}

function formatTime(t: string) {
  if (!t) return '-'
  return new Date(t).toLocaleString('zh-CN')
}
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 16px;
}
</style>
