<template>
  <div>
    <div class="page-header">
      <el-input
        v-model="searchJobId"
        placeholder="按打印任务 ID 搜索..."
        clearable
        style="width: 280px"
        @clear="load"
        @keyup.enter="load"
      />
      <el-button type="primary" @click="load">刷新</el-button>
    </div>

    <el-table :data="list" stripe v-loading="loading" @expand-change="onExpand">
      <el-table-column type="expand" width="30">
        <template #default="{ row }">
          <div class="detail-wrap" v-if="row.details?.length">
            <el-table :data="row.details" stripe size="small">
              <el-table-column label="Tray" width="70" align="center">
                <template #default="{ row: d }">
                  <el-tag v-if="d.tray > 0" size="small">T{{ d.tray }}</el-tag>
                  <el-tag v-else size="small" type="info">EXT</el-tag>
                </template>
              </el-table-column>
              <el-table-column label="料盘" min-width="140" show-overflow-tooltip>
                <template #default="{ row: d }">{{ d.spool_name || '-' }}</template>
              </el-table-column>
              <el-table-column label="使用长度" width="110">
                <template #default="{ row: d }">{{ d.filament_used_mm?.toFixed(0) }}mm</template>
              </el-table-column>
              <el-table-column label="使用重量" width="100">
                <template #default="{ row: d }">{{ d.filament_used_weight?.toFixed(1) }}g</template>
              </el-table-column>
              <el-table-column label="扣减" width="80" align="center">
                <template #default="{ row: d }">
                  <el-tag v-if="d.deducted" type="success" size="small">已扣减</el-tag>
                  <el-tag v-else type="warning" size="small">未扣减</el-tag>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="110" fixed="right">
                <template #default="{ row: d }">
                  <el-button
                    size="small"
                    type="warning"
                    :disabled="d.deducted || !d.spool_name"
                    :loading="deductingId === d.id"
                    @click="handleDeduct(d)"
                  >
                    手动扣减
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
          <el-empty v-else description="无明细" />
        </template>
      </el-table-column>
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="printer_name" label="打印机" width="100" />
      <el-table-column label="文件" min-width="180" show-overflow-tooltip>
        <template #default="{ row }">{{ row.filename || row.print_job_id }}</template>
      </el-table-column>
      <el-table-column label="料盘数" width="80" align="center">
        <template #default="{ row }">
          {{ row.details?.length || 0 }}
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="80">
        <template #default="{ row }">
          <el-tag :type="statusType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="start_time" label="开始" width="160">
        <template #default="{ row }">{{ formatTime(row.start_time) }}</template>
      </el-table-column>
      <el-table-column label="结束" width="160">
        <template #default="{ row }">{{ formatTime(row.end_time) }}</template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { printRecordApi } from '@/api'
import { ElMessage } from 'element-plus'

const list = ref<any[]>([])
const loading = ref(false)
const searchJobId = ref('')
const deductingId = ref<number | null>(null)

onMounted(() => load())

async function load() {
  loading.value = true
  try {
    const params: any = { limit: 200 }
    if (searchJobId.value) {
      params.print_job_id = searchJobId.value
    }
    const res = await printRecordApi.list(params)
    list.value = res.data
  } finally {
    loading.value = false
  }
}

async function handleDeduct(detail: any) {
  deductingId.value = detail.id
  try {
    await printRecordApi.deductDetail(detail.id)
    ElMessage.success(`已从料盘「${detail.spool_name}」扣减 ${detail.filament_used_weight?.toFixed(1)}g`)
    await load()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '扣减失败')
  } finally {
    deductingId.value = null
  }
}

function statusType(s: string) {
  if (s === 'finished') return 'success'
  if (s === 'failed') return 'danger'
  return 'warning'
}

function statusLabel(s: string) {
  if (s === 'finished') return '完成'
  if (s === 'failed') return '失败'
  return '打印中'
}

function formatTime(t: string) {
  if (!t) return '-'
  return new Date(t).toLocaleString('zh-CN')
}

function onExpand(row: any) {
  // expand handler
}
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 16px;
}
.detail-wrap {
  padding: 8px 0;
}
</style>
