<template>
  <div>
    <div class="page-header">
      <el-button type="primary" @click="openDialog()">
        <el-icon><Plus /></el-icon> 新增耗材
      </el-button>
    </div>
    <el-table :data="list" stripe v-loading="loading">
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column label="颜色" width="60">
        <template #default="{ row }">
          <div class="color-dot" :style="{ background: row.color }" />
        </template>
      </el-table-column>
      <el-table-column prop="name" label="名称" min-width="150" />
      <el-table-column prop="manufacturer_name" label="厂商" width="140" />
      <el-table-column prop="filament_type" label="类型" width="90" />
      <el-table-column prop="color_name" label="颜色名" width="100" />
      <el-table-column prop="diameter" label="直径(mm)" width="100" />
      <el-table-column prop="density" label="密度(g/cm³)" width="110" />
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

    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑耗材' : '新增耗材'" width="550px">
      <el-form :model="form" label-width="110px">
        <el-form-item label="所属厂商" required>
          <el-select v-model="form.manufacturer_id" filterable style="width:100%">
            <el-option v-for="m in manufacturers" :key="m.id" :label="m.name" :value="m.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="名称" required>
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="类型" required>
          <el-select v-model="form.filament_type" style="width:100%">
            <el-option label="PLA" value="PLA" />
            <el-option label="PETG" value="PETG" />
            <el-option label="ABS" value="ABS" />
            <el-option label="TPU" value="TPU" />
            <el-option label="PA (尼龙)" value="PA" />
            <el-option label="PC" value="PC" />
            <el-option label="ASA" value="ASA" />
            <el-option label="PET" value="PET" />
            <el-option label="PP" value="PP" />
            <el-option label="PVA" value="PVA" />
            <el-option label="其他" value="OTHER" />
          </el-select>
        </el-form-item>
        <el-form-item label="颜色">
          <el-input v-model="form.color" placeholder="#FFFFFF">
            <template #prepend>
              <el-color-picker v-model="form.color" show-alpha size="small" />
            </template>
          </el-input>
        </el-form-item>
        <el-form-item label="颜色名">
          <el-input v-model="form.color_name" />
        </el-form-item>
        <el-form-item label="直径(mm)">
          <el-input-number v-model="form.diameter" :min="1" :max="3" :step="0.05" :precision="2" />
        </el-form-item>
        <el-form-item label="密度(g/cm³)" required>
          <el-input-number v-model="form.density" :min="0.5" :max="3" :step="0.01" :precision="2" />
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
import { filamentApi, manufacturerApi } from '@/api'
import { ElMessage } from 'element-plus'

const list = ref<any[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)
const saving = ref(false)
const manufacturers = ref<any[]>([])
const editId = ref<number | null>(null)
const form = ref({
  manufacturer_id: null as number | null,
  name: '',
  filament_type: 'PLA',
  color: '#FFFFFF',
  color_name: '',
  diameter: 1.75,
  density: 1.24,
})

onMounted(async () => {
  await Promise.all([load(), loadManufacturers()])
})

async function load() {
  loading.value = true
  try {
    const res = await filamentApi.list()
    list.value = res.data
  } finally {
    loading.value = false
  }
}

async function loadManufacturers() {
  const res = await manufacturerApi.list()
  manufacturers.value = res.data
}

function openDialog(row?: any) {
  loadManufacturers()
  if (row) {
    isEdit.value = true
    editId.value = row.id
    form.value = {
      manufacturer_id: row.manufacturer_id,
      name: row.name,
      filament_type: row.filament_type,
      color: row.color || '#FFFFFF',
      color_name: row.color_name || '',
      diameter: row.diameter,
      density: row.density,
    }
  } else {
    isEdit.value = false
    editId.value = null
    form.value = {
      manufacturer_id: null,
      name: '',
      filament_type: 'PLA',
      color: '#FFFFFF',
      color_name: '',
      diameter: 1.75,
      density: 1.24,
    }
  }
  dialogVisible.value = true
}

async function handleSave() {
  saving.value = true
  try {
    if (isEdit.value && editId.value) {
      await filamentApi.update(editId.value, form.value)
      ElMessage.success('已更新')
    } else {
      await filamentApi.create(form.value)
      ElMessage.success('已创建')
    }
    dialogVisible.value = false
    await load()
  } finally {
    saving.value = false
  }
}

async function handleDelete(id: number) {
  await filamentApi.delete(id)
  ElMessage.success('已删除')
  await load()
}
</script>

<style scoped>
.page-header { margin-bottom: 16px; }
.color-dot { width: 20px; height: 20px; border-radius: 4px; border: 1px solid #dcdfe6; }
</style>
