<template>
  <el-tooltip :content="statusText" placement="bottom">
    <el-tag :type="tagType" size="small" effect="dark">
      <el-icon style="margin-right: 4px; vertical-align: middle">
        <Connection />
      </el-icon>
      {{ statusText }}
    </el-tag>
  </el-tooltip>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  connected?: boolean
  status?: string
}>()

const tagType = computed(() => {
  if (!props.connected) return 'danger'
  if (props.status === 'running') return 'success'
  if (props.status === 'pause') return 'warning'
  return 'info'
})

const statusText = computed(() => {
  if (!props.connected) return '离线'
  if (props.status === 'running') return '打印中'
  if (props.status === 'pause') return '已暂停'
  if (props.status === 'finish') return '已完成'
  return '空闲'
})
</script>
