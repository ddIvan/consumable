<template>
  <div>
    <div class="page-header">
      <el-button type="primary" @click="openDialog()">
        <el-icon><Plus /></el-icon> 新增厂商
      </el-button>
    </div>
    <el-table :data="list" stripe v-loading="loading">
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="name" label="名称" min-width="160" />
      <el-table-column prop="short_name" label="简称" width="120" />
      <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
      <el-table-column prop="website" label="网站" min-width="180">
        <template #default="{ row }">
          <el-link v-if="row.website" :href="row.website" target="_blank" type="primary">{{ row.website }}</el-link>
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

    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑厂商' : '新增厂商'" width="500px">
      <el-form :model="form" label-width="80px" @submit.prevent="handleSave">
        <el-form-item label="名称" required>
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="简称">
          <el-input v-model="form.short_name" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="网站">
          <el-input v-model="form.website" placeholder="https://" />
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
import { manufacturerApi } from '@/api'
import { ElMessage } from 'element-plus'

const list = ref<any[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)
const saving = ref(false)
const form = ref({ name: '', short_name: '', description: '', website: '' })
const editId = ref<number | null>(null)

onMounted(() => load())

async function load() {
  loading.value = true
  try {
    const res = await manufacturerApi.list()
    list.value = res.data
  } finally {
    loading.value = false
  }
}

function openDialog(row?: any) {
  if (row) {
    isEdit.value = true
    editId.value = row.id
    form.value = { name: row.name, short_name: row.short_name || '', description: row.description || '', website: row.website || '' }
  } else {
    isEdit.value = false
    editId.value = null
    form.value = { name: '', short_name: '', description: '', website: '' }
  }
  dialogVisible.value = true
}

async function handleSave() {
  saving.value = true
  try {
    if (isEdit.value && editId.value) {
      await manufacturerApi.update(editId.value, form.value)
      ElMessage.success('已更新')
    } else {
      await manufacturerApi.create(form.value)
      ElMessage.success('已创建')
    }
    dialogVisible.value = false
    await load()
  } finally {
    saving.value = false
  }
}

async function handleDelete(id: number) {
  await manufacturerApi.delete(id)
  ElMessage.success('已删除')
  await load()
}
</script>

<style scoped>
.page-header { margin-bottom: 16px; }
</style>
