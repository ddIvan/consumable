<template>
  <div>
    <div class="page-header">
      <div class="header-left">
        <el-input
          v-model="search"
          placeholder="搜索消息内容 / 主题 / 打印机..."
          clearable
          style="width: 320px"
          @clear="load"
          @keyup.enter="load"
        />
        <el-button type="primary" @click="load">查询</el-button>
      </div>
      <el-button type="danger" :disabled="!list.length" @click="handleClear">
        清空全部
      </el-button>
    </div>

    <el-table :data="list" stripe v-loading="loading" @expand-change="onExpand">
      <el-table-column type="expand" width="30">
        <template #default="{ row }">
          <pre class="payload-view">{{ formatPayload(row.payload) }}</pre>
        </template>
      </el-table-column>
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="printer_name" label="打印机" width="100" />
      <el-table-column label="主题" min-width="220" show-overflow-tooltip>
        <template #default="{ row }">{{ row.topic }}</template>
      </el-table-column>
      <el-table-column label="消息预览" min-width="300" show-overflow-tooltip>
        <template #default="{ row }">{{ previewPayload(row.payload) }}</template>
      </el-table-column>
      <el-table-column label="接收时间" width="180">
        <template #default="{ row }">{{ formatTime(row.received_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="80" fixed="right">
        <template #default="{ row }">
          <el-button size="small" type="danger" link @click="handleDelete(row.id)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { mqttMessageApi } from '@/api'
import { ElMessage, ElMessageBox } from 'element-plus'

const list = ref<any[]>([])
const loading = ref(false)
const search = ref('')

onMounted(() => load())

async function load() {
  loading.value = true
  try {
    const res = await mqttMessageApi.list({
      search: search.value,
      limit: 200,
    })
    list.value = res.data
  } finally {
    loading.value = false
  }
}

function previewPayload(payload: string) {
  try {
    const obj = JSON.parse(payload)
    const str = JSON.stringify(obj)
    return str.length > 120 ? str.slice(0, 120) + '...' : str
  } catch {
    return payload.slice(0, 120)
  }
}

function formatPayload(payload: string) {
  try {
    return JSON.stringify(JSON.parse(payload), null, 2)
  } catch {
    return payload
  }
}

function formatTime(t: string) {
  if (!t) return '-'
  return new Date(t).toLocaleString('zh-CN')
}

function onExpand(row: any) {
  // expand handler
}

async function handleDelete(id: number) {
  await mqttMessageApi.delete(id)
  ElMessage.success('已删除')
  await load()
}

async function handleClear() {
  try {
    await ElMessageBox.confirm('确定要清空所有 MQTT 消息记录吗？', '确认', {
      type: 'warning',
    })
    await mqttMessageApi.clear()
    ElMessage.success('已清空')
    await load()
  } catch {
    // cancelled
  }
}
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 16px;
}
.header-left {
  display: flex;
  gap: 8px;
}
.payload-view {
  background: #f5f7fa;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  padding: 12px;
  margin: 8px 0;
  font-size: 13px;
  line-height: 1.5;
  max-height: 400px;
  overflow-y: auto;
  white-space: pre-wrap;
  word-break: break-all;
}
</style>
