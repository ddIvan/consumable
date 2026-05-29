<template>
  <div>
    <div class="page-header">
      <el-button type="primary" @click="openDialog()">
        <el-icon><Plus /></el-icon> 新增打印机
      </el-button>
    </div>
    <el-table :data="list" stripe v-loading="loading">
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="name" label="名称" width="140" />
      <el-table-column prop="serial" label="序列号" width="160" />
      <el-table-column prop="ip_address" label="IP 地址" width="140" />
      <el-table-column prop="port" label="端口" width="80" />
      <el-table-column prop="is_active" label="状态" width="80">
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
            {{ row.is_active ? '启用' : '禁用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="连接" width="120">
        <template #default="{ row }">
          <el-button
            size="small"
            :type="connectedIds.has(row.id) ? 'danger' : 'success'"
            @click="toggleConnect(row)"
          >
            {{ connectedIds.has(row.id) ? '断开' : '连接' }}
          </el-button>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="160" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="openDialog(row)">编辑</el-button>
          <el-popconfirm title="确认删除?" @confirm="handleDelete(row.id)">
            <template #reference>
              <el-button size="small" type="danger">删除</el-button>
            </template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑打印机' : '新增打印机'" width="500px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="名称" required>
          <el-input v-model="form.name" placeholder="例如: 书房P1S" />
        </el-form-item>
        <el-form-item label="序列号" required>
          <el-input v-model="form.serial" placeholder="打印机背面标签上的序列号" />
        </el-form-item>
        <el-form-item label="IP 地址" required>
          <el-input v-model="form.ip_address" placeholder="192.168.x.x" />
        </el-form-item>
        <el-form-item label="访问码" required>
          <el-input v-model="form.access_code" placeholder="打印机屏幕上的访问码" show-password />
        </el-form-item>
        <el-form-item label="MQTT 端口">
          <el-input-number v-model="form.port" :min="1" :max="65535" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { printerApi } from '@/api'
import { ElMessage } from 'element-plus'

const list = ref<any[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)
const saving = ref(false)
const editId = ref<number | null>(null)
const connectedIds = ref(new Set<number>())
const form = ref({
  name: '',
  serial: '',
  ip_address: '',
  access_code: '',
  port: 8883,
})

onMounted(() => load())

async function load() {
  loading.value = true
  try {
    const res = await printerApi.list()
    list.value = res.data
  } finally {
    loading.value = false
  }
}

function openDialog(row?: any) {
  if (row) {
    isEdit.value = true
    editId.value = row.id
    form.value = {
      name: row.name,
      serial: row.serial,
      ip_address: row.ip_address,
      access_code: '',
      port: row.port || 8883,
    }
  } else {
    isEdit.value = false
    editId.value = null
    form.value = { name: '', serial: '', ip_address: '', access_code: '', port: 8883 }
  }
  dialogVisible.value = true
}

async function handleSave() {
  saving.value = true
  try {
    if (isEdit.value && editId.value) {
      const payload = { ...form.value }
      if (!payload.access_code) delete (payload as any).access_code
      await printerApi.update(editId.value, payload)
      ElMessage.success('已更新')
    } else {
      await printerApi.create(form.value)
      ElMessage.success('已创建')
    }
    dialogVisible.value = false
    await load()
  } finally {
    saving.value = false
  }
}

async function handleDelete(id: number) {
  await printerApi.delete(id)
  ElMessage.success('已删除')
  await load()
}

async function toggleConnect(row: any) {
  if (connectedIds.value.has(row.id)) {
    await printerApi.disconnect(row.id)
    connectedIds.value.delete(row.id)
    ElMessage.info('已断开')
  } else {
    try {
      const res = await printerApi.connect(row.id)
      if (res.data.status === 'connected') {
        connectedIds.value.add(row.id)
        ElMessage.success('已连接')
      } else {
        ElMessage.error(res.data.message || '连接失败')
      }
    } catch {
      ElMessage.error('连接失败，请检查打印机状态')
    }
  }
}
</script>

<style scoped>
.page-header { margin-bottom: 16px; }
</style>
