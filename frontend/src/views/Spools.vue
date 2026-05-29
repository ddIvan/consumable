<template>
  <div>
    <div class="page-header">
      <el-button type="primary" @click="openDialog()">
        <el-icon><Plus /></el-icon> 新增料盘
      </el-button>
    </div>
    <el-table :data="list" stripe v-loading="loading">
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column label="颜色" width="50">
        <template #default="{ row }">
          <div class="color-dot" :style="{ background: row.filament_color }" />
        </template>
      </el-table-column>
      <el-table-column prop="name" label="名称" width="150" />
      <el-table-column prop="manufacturer_name" label="厂商" width="120" />
      <el-table-column prop="filament_type" label="类型" width="80" />
      <el-table-column prop="initial_weight" label="初始重量" width="100">
        <template #default="{ row }">{{ row.initial_weight }}g</template>
      </el-table-column>
      <el-table-column prop="current_weight" label="当前余量" width="100">
        <template #default="{ row }">{{ row.current_weight }}g</template>
      </el-table-column>
      <el-table-column label="剩余" width="120">
        <template #default="{ row }">
          <el-progress
            :percentage="Math.round(row.current_weight / row.initial_weight * 100)"
            :stroke-width="14"
            :color="progressColor(row.current_weight / row.initial_weight * 100)"
          />
        </template>
      </el-table-column>
      <el-table-column label="位置" width="100">
        <template #default="{ row }">
          <el-tag v-if="row.location === 'AMS'" type="primary" size="small">
            AMS T{{ row.ams_tray }}
          </el-tag>
          <el-tag v-else-if="row.location === 'EXT'" type="warning" size="small">外置</el-tag>
          <el-tag v-else type="info" size="small">仓库</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="80">
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
            {{ row.is_active ? '活跃' : '闲置' }}
          </el-tag>
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

    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑料盘' : '新增料盘'" width="500px">
      <el-form :model="form" label-width="110px">
        <el-form-item label="耗材" required>
          <el-select v-model="form.filament_id" filterable style="width:100%">
            <el-option
              v-for="f in filaments"
              :key="f.id"
              :label="`[${f.manufacturer_name}] ${f.name} (${f.filament_type})`"
              :value="f.id"
            >
              <span>{{ f.manufacturer_name }} - {{ f.name }} ({{ f.filament_type }})</span>
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="料盘名称" required>
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="标签">
          <el-input v-model="form.label" placeholder="自定义标签" />
        </el-form-item>
        <el-form-item label="初始重量(g)" required>
          <el-input-number v-model="form.initial_weight" :min="1" :max="5000" :step="100" />
        </el-form-item>
        <el-form-item label="当前余量(g)" required>
          <el-input-number v-model="form.current_weight" :min="0" :max="5000" :step="10" />
        </el-form-item>
        <el-form-item label="AMS 位置">
          <el-select v-model="form.ams_tray" style="width:100%">
            <el-option label="不在 AMS 中" :value="0" />
            <el-option label="AMS Tray 1" :value="1" />
            <el-option label="AMS Tray 2" :value="2" />
            <el-option label="AMS Tray 3" :value="3" />
            <el-option label="AMS Tray 4" :value="4" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="form.is_active" active-text="活跃" inactive-text="闲置" />
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
import { spoolApi, filamentApi } from '@/api'
import { ElMessage } from 'element-plus'

const list = ref<any[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)
const saving = ref(false)
const filaments = ref<any[]>([])
const editId = ref<number | null>(null)
const form = ref({
  filament_id: null as number | null,
  name: '',
  label: '',
  initial_weight: 1000,
  current_weight: 1000,
  is_active: true,
  ams_tray: 0,
})

onMounted(() => load())

async function load() {
  loading.value = true
  try {
    const [spoolRes, filamentRes] = await Promise.all([
      spoolApi.list(),
      filamentApi.list(),
    ])
    list.value = spoolRes.data
    filaments.value = filamentRes.data
  } finally {
    loading.value = false
  }
}

function openDialog(row?: any) {
  filamentApi.list().then((res) => { filaments.value = res.data })
  if (row) {
    isEdit.value = true
    editId.value = row.id
    form.value = {
      filament_id: row.filament_id,
      name: row.name,
      label: row.label || '',
      initial_weight: row.initial_weight,
      current_weight: row.current_weight,
      is_active: row.is_active,
      ams_tray: row.ams_tray || 0,
    }
  } else {
    isEdit.value = false
    editId.value = null
    form.value = {
      filament_id: null,
      name: '',
      label: '',
      initial_weight: 1000,
      current_weight: 1000,
      is_active: true,
      ams_tray: 0,
    }
  }
  dialogVisible.value = true
}

async function handleSave() {
  saving.value = true
  try {
    if (isEdit.value && editId.value) {
      await spoolApi.update(editId.value, form.value)
      ElMessage.success('已更新')
    } else {
      await spoolApi.create(form.value)
      ElMessage.success('已创建')
    }
    dialogVisible.value = false
    await load()
  } finally {
    saving.value = false
  }
}

async function handleDelete(id: number) {
  await spoolApi.delete(id)
  ElMessage.success('已删除')
  await load()
}

function progressColor(pct: number) {
  if (pct > 50) return '#67c23a'
  if (pct > 20) return '#e6a23c'
  return '#f56c6c'
}
</script>

<style scoped>
.page-header { margin-bottom: 16px; }
.color-dot { width: 20px; height: 20px; border-radius: 4px; border: 1px solid #dcdfe6; }
</style>
