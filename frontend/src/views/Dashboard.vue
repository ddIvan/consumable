<template>
  <div class="dashboard">
    <!-- Summary Cards -->
    <el-row :gutter="16" class="mb-4">
      <el-col :span="6">
        <el-card shadow="hover" :body-style="{ padding: '14px 20px' }">
          <div class="stat-card">
            <div class="stat-value">{{ summary.total_spools }}</div>
            <div class="stat-label">总料盘</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" :body-style="{ padding: '14px 20px' }">
          <div class="stat-card">
            <div class="stat-value">{{ summary.total_filaments }}g</div>
            <div class="stat-label">剩余耗材总量</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" :body-style="{ padding: '14px 20px' }">
          <div class="stat-card">
            <div class="stat-value">{{ locData.ams.total_spools + locData.ext.total_spools }}</div>
            <div class="stat-label">在线料盘 (AMS+EXT)</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" :body-style="{ padding: '14px 20px' }">
          <div class="stat-card">
            <div class="stat-value">{{ locData.warehouse.total_spools }}</div>
            <div class="stat-label">仓库库存</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Printer Status -->
    <el-card shadow="hover" class="mb-4" v-if="printerConnected">
      <template #header>
        <span><el-icon><Monitor /></el-icon> 打印机实时状态</span>
      </template>
      <el-row :gutter="20">
        <el-col :span="6">
          <div class="sensor-item">
            <span class="sensor-label">喷嘴</span>
            <span class="sensor-value" :class="{ hot: printer.nozzle_temp > 0 }">
              {{ printer.nozzle_temp }}°C / {{ printer.nozzle_target }}°C
            </span>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="sensor-item">
            <span class="sensor-label">热床</span>
            <span class="sensor-value" :class="{ hot: printer.bed_temp > 0 }">
              {{ printer.bed_temp }}°C / {{ printer.bed_target }}°C
            </span>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="sensor-item">
            <span class="sensor-label">打印进度</span>
            <el-progress :percentage="printer.mc_percent" :stroke-width="16" />
          </div>
        </el-col>
        <el-col :span="6">
          <div class="sensor-item">
            <span class="sensor-label">耗材余量</span>
            <el-progress :percentage="Math.round(printer.mc_remaining_percent)" :stroke-width="16" :color="pColor" />
          </div>
        </el-col>
      </el-row>
      <el-row class="mt-3">
        <el-col :span="24">
          <div class="print-file-info">
            <el-tag size="small" type="info">{{ printer.gcode_file || '无活跃打印' }}</el-tag>
            <el-tag size="small" type="warning" v-if="printer.gcode_state === 'running'">
              已用耗材: {{ printer.filament_used_mm.toFixed(0) }}mm
            </el-tag>
          </div>
        </el-col>
      </el-row>
    </el-card>

    <!-- ═══════════════ AMS + EXT 同一行 4:1 ═══════════════ -->
    <el-card shadow="hover" class="mb-4">
      <template #header>
        <div class="section-header">
          <span><el-icon><Coin /></el-icon> AMS + EXT</span>
          <el-tag type="info" size="small">
            AMS {{ locData.ams.total_remaining }}g / EXT {{ locData.ext.total_remaining }}g
          </el-tag>
        </div>
      </template>

      <div class="ams-ext-row">
        <!-- ─── AMS: 4 trays ─── -->
        <div class="ams-section">
          <div class="tray-row">
            <template v-for="i in 4" :key="'slot-' + i">
              <div v-if="trayMap[i]" class="tray-cell">
                <div class="tray-label">T{{ i }}</div>
                <div
                  class="tank"
                  :style="{
                    '--water-pct': trayMap[i].remaining_pct + '%',
                    '--water-clr': trayMap[i].filament_color,
                  }"
                >
                  <div class="wave" :style="{ bottom: trayMap[i].remaining_pct + '%' }"></div>
                  <span class="pct" :style="{ color: contrastColor(trayMap[i].filament_color) }">{{ trayMap[i].remaining_pct }}%</span>
                </div>
                <div class="info">
                  <div class="dot" :style="{ background: trayMap[i].filament_color }"></div>
                  <div class="name" :title="trayMap[i].name">{{ trayMap[i].name }}</div>
                  <div class="meta">{{ trayMap[i].manufacturer_name }} · {{ trayMap[i].filament_type }}</div>
                  <div class="w">{{ trayMap[i].current_weight }}g / {{ trayMap[i].initial_weight }}g</div>
                </div>
              </div>
              <div v-else class="tray-cell tray-empty">
                <div class="tray-label">T{{ i }}</div>
                <div class="tank tank-empty-bg">
                  <span class="pct van">--</span>
                </div>
                <div class="info">
                  <div class="empty-text">空闲</div>
                </div>
              </div>
            </template>
          </div>
        </div>

        <!-- ─── EXT: 1 slot ─── -->
        <div class="ext-section">
          <div class="tray-cell" v-if="firstExt">
            <div class="tray-label ext-label">EXT</div>
            <div
              class="tank"
              :style="{
                '--water-pct': firstExt.remaining_pct + '%',
                '--water-clr': firstExt.filament_color,
              }"
            >
              <div class="wave" :style="{ bottom: firstExt.remaining_pct + '%' }"></div>
              <span class="pct" :style="{ color: contrastColor(firstExt.filament_color) }">{{ firstExt.remaining_pct }}%</span>
            </div>
            <div class="info">
              <div class="dot" :style="{ background: firstExt.filament_color }"></div>
              <div class="name" :title="firstExt.name">{{ firstExt.name }}</div>
              <div class="meta">{{ firstExt.manufacturer_name }} · {{ firstExt.filament_type }}</div>
              <div class="w">{{ firstExt.current_weight }}g / {{ firstExt.initial_weight }}g</div>
              <div v-if="(locData.ext.spools || []).length > 1" class="ext-more">
                +{{ (locData.ext.spools || []).length - 1 }} 备用
              </div>
            </div>
          </div>
          <div class="tray-cell tray-empty" v-else>
            <div class="tray-label ext-label">EXT</div>
            <div class="tank tank-empty-bg">
              <span class="pct van">--</span>
            </div>
            <div class="info">
              <div class="empty-text">无外置耗材</div>
            </div>
          </div>
        </div>
      </div>
    </el-card>

    <!-- ═══════════════ 仓库库存 ═══════════════ -->
    <el-card shadow="hover" class="mb-4">
      <template #header>
        <div class="section-header">
          <span><el-icon><Box /></el-icon> 仓库库存</span>
          <el-tag type="info" size="small">
            {{ locData.warehouse.total_spools }}盘 / {{ locData.warehouse.total_remaining }}g / {{ locData.warehouse.remaining_pct }}%
          </el-tag>
        </div>
      </template>
      <el-row :gutter="16" v-if="locData.warehouse.spools && locData.warehouse.spools.length > 0">
        <el-col :span="8" v-for="s in locData.warehouse.spools" :key="s.id">
          <div class="warehouse-item">
            <div class="wh-left">
              <div class="wh-color" :style="{ background: s.filament_color }"></div>
              <div class="wh-info">
                <div class="wh-name">{{ s.name }}</div>
                <div class="wh-meta">{{ s.manufacturer_name }} · {{ s.filament_type }}</div>
              </div>
            </div>
            <div class="wh-right">
              <el-progress :percentage="s.remaining_pct" :stroke-width="12" :color="pColor" />
              <div class="wh-weight">{{ s.current_weight }}g / {{ s.initial_weight }}g</div>
            </div>
          </div>
        </el-col>
      </el-row>
      <el-empty v-else description="仓库无库存" :image-size="80" />
    </el-card>

    <!-- Recent Records -->
    <el-card shadow="hover">
      <template #header>
        <span><el-icon><Document /></el-icon> 最近打印记录</span>
      </template>
      <el-table :data="summary.recent_records || []" size="small" stripe>
        <el-table-column prop="filename" label="文件" min-width="200" show-overflow-tooltip />
        <el-table-column prop="spool_name" label="料盘" width="140" />
        <el-table-column prop="filament_used_mm" label="使用长度" width="120">
          <template #default="{ row }">{{ row.filament_used_mm.toFixed(0) }}mm</template>
        </el-table-column>
        <el-table-column prop="filament_used_weight" label="使用重量" width="120">
          <template #default="{ row }">{{ row.filament_used_weight.toFixed(1) }}g</template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="row.status === 'finished' ? 'success' : 'warning'" size="small">
              {{ row.status === 'finished' ? '完成' : row.status === 'failed' ? '失败' : '打印中' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="时间" width="170">
          <template #default="{ row }">{{ fmt(row.created_at) }}</template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { dashboardApi } from '@/api'

const summary = ref<any>({
  total_spools: 0, active_spools: 0, total_filaments: 0,
  spools: [], recent_records: [],
})
const locData = ref<any>({
  ams: { total_spools: 0, total_remaining: 0, remaining_pct: 0, ams_trays: [], spools: [] },
  ext: { total_spools: 0, total_remaining: 0, remaining_pct: 0, spools: [] },
  warehouse: { total_spools: 0, total_remaining: 0, remaining_pct: 0, spools: [] },
})

const printer = ref<any>({
  connected: false, gcode_state: 'idle', gcode_file: '',
  mc_percent: 0, nozzle_temp: 0, nozzle_target: 0,
  bed_temp: 0, bed_target: 0, filament_used_mm: 0, mc_remaining_percent: 100,
})

const printerConnected = computed(() => summary.value.printer_status?.connected || false)
const printerRunning = computed(() => summary.value.printer_status?.gcode_state === 'running')

/** Build trayMap[1..4] for quick lookup */
const trayMap = computed(() => {
  const map: Record<number, any> = {}
  for (const t of (locData.value.ams.ams_trays || [])) {
    map[t.tray] = t
  }
  return map
})

const firstExt = computed(() => {
  const spools = locData.value.ext.spools || []
  return spools.length > 0 ? spools[0] : null
})

let pollTimer: number | null = null

onMounted(async () => {
  await loadAll()
  pollTimer = window.setInterval(loadAll, 10000)
})

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
})

async function loadAll() {
  try {
    const [sumRes, locRes] = await Promise.all([
      dashboardApi.summary(),
      dashboardApi.locations(),
    ])
    summary.value = sumRes.data
    locData.value = locRes.data
    if (sumRes.data.printer_status) {
      printer.value = sumRes.data.printer_status
    }
  } catch (e) {
    console.error(e)
  }
}

function pColor(pct: number) {
  if (pct > 50) return '#67c23a'
  if (pct > 20) return '#e6a23c'
  return '#f56c6c'
}

function hexToRgba(hex: string, alpha: number) {
  let h = hex.replace('#', '')
  if (h.length === 3) h = h[0] + h[0] + h[1] + h[1] + h[2] + h[2]
  const r = parseInt(h.substring(0, 2), 16)
  const g = parseInt(h.substring(2, 4), 16)
  const b = parseInt(h.substring(4, 6), 16)
  return `rgba(${r},${g},${b},${alpha})`
}

/** Return white or dark text color based on background luminance. */
function contrastColor(bgHex: string) {
  let h = bgHex.replace('#', '')
  if (h.length === 3) h = h[0] + h[0] + h[1] + h[1] + h[2] + h[2]
  const r = parseInt(h.substring(0, 2), 16)
  const g = parseInt(h.substring(2, 4), 16)
  const b = parseInt(h.substring(4, 6), 16)
  // relative luminance (perceived brightness)
  const lum = (0.299 * r + 0.587 * g + 0.114 * b) / 255
  return lum > 0.5 ? '#1d1e1f' : '#ffffff'
}

function fmt(t: string) {
  if (!t) return '-'
  return new Date(t).toLocaleString('zh-CN')
}
</script>

<style scoped>
.mb-4 { margin-bottom: 16px; }
.mt-3 { margin-top: 12px; }

/* ── Summary cards ── */
.stat-card { text-align: center; padding: 2px 0; }
.stat-value { font-size: 22px; font-weight: 700; color: #303133; }
.stat-label { font-size: 13px; color: #909399; margin-top: 2px; }

/* ── Printer ── */
.sensor-item { padding: 4px 0; }
.sensor-label { font-size: 12px; color: #909399; display: block; margin-bottom: 4px; }
.sensor-value { font-size: 16px; font-weight: 600; }
.sensor-value.hot { color: #f56c6c; }
.print-file-info { display: flex; gap: 8px; align-items: center; }
.section-header { display: flex; align-items: center; justify-content: space-between; }

/* ════════════════════ AMS + EXT 4:1 Row ════════════════════ */

.ams-ext-row { display: flex; gap: 16px; }
.ams-section { flex: 4; min-width: 0; }
.ext-section {
  flex: 1; min-width: 0;
  border-left: 2px solid #ebeef5;
  padding-left: 16px;
}

/* ── Tray grid ── */
.tray-row { display: flex; gap: 12px; }
.tray-cell {
  flex: 1; text-align: center; padding: 12px 8px;
  border-radius: 10px; background: #fff;
  border: 1px solid #ebeef5;
  transition: box-shadow 0.2s;
}
.tray-cell:hover { box-shadow: 0 2px 12px rgba(0,0,0,0.08); }
.tray-empty { border-style: dashed; background: #fafafa; }

.tray-label {
  font-size: 12px; font-weight: 700; color: #606266;
  background: #f0f2f5; display: inline-block;
  padding: 1px 14px; border-radius: 8px; margin-bottom: 10px;
}
.ext-label { background: #fdf6ec; color: #e6a23c; }

/* ════════════════════ Water Tank ════════════════════ */
.tank {
  position: relative;
  width: 72px; height: 148px;
  margin: 0 auto 10px;
  border: 2px solid #b0b4b8;
  border-radius: 10px 10px 8px 8px;
  overflow: hidden;
  box-shadow: inset 0 1px 4px rgba(0,0,0,0.06);
  /* empty portion — always light gray; water fill via ::before */
  background: #edeff2;
}
/* colored water fill — rises from bottom */
.tank::before {
  content: '';
  position: absolute;
  bottom: 0; left: 0; right: 0;
  height: var(--water-pct, 0%);
  background: var(--water-clr, #ccc);
  border-radius: 0 0 7px 7px;
  transition: height 0.6s ease;
  pointer-events: none;
  z-index: 0;
}
/* depth shimmer on water surface */
.tank::after {
  content: '';
  position: absolute;
  bottom: 0; left: 0; right: 0;
  height: var(--water-pct, 0%);
  background: linear-gradient(
    180deg,
    rgba(255,255,255,0.15) 0%,
    transparent 35%,
    rgba(0,0,0,0.08) 100%
  );
  border-radius: 0 0 7px 7px;
  pointer-events: none;
  transition: height 0.6s ease;
  z-index: 0;
}
.tank-empty-bg {
  background: #edeff2;
  border-style: dashed; border-color: #d0d4d8;
}

/* ── Surface wave arc ── */
.wave {
  position: absolute;
  height: 7px;
  background: rgba(255,255,255,0.22);
  border-radius: 50%;
  left: -4%; width: 108%;
  pointer-events: none;
  z-index: 1;
  animation: sway 3s ease-in-out infinite alternate;
}
@keyframes sway {
  0%   { transform: translateX(-3px) scaleY(1); }
  100% { transform: translateX(3px) scaleY(1.5); }
}

/* ── Percentage overlay ── */
.pct {
  position: absolute;
  top: 50%; left: 50%;
  transform: translate(-50%, -50%);
  font-size: 17px; font-weight: 800;
  /* color set inline via contrastColor() */
  text-shadow:
    0 0 5px rgba(0,0,0,0.35),
    0 0 10px rgba(255,255,255,0.25);
  z-index: 3;
  pointer-events: none;
  line-height: 1;
}
.pct.van { color: #c0c4cc; text-shadow: none; }

/* ── Info below tank ── */
.info { display: flex; flex-direction: column; align-items: center; gap: 2px; }
.dot { width: 16px; height: 16px; border-radius: 4px; border: 1px solid #dcdfe6; }
.name { font-size: 12px; font-weight: 600; color: #303133; max-width: 100%; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.meta { font-size: 11px; color: #909399; line-height: 1.2; }
.w { font-size: 11px; color: #606266; }
.empty-text { font-size: 13px; color: #c0c4cc; padding: 16px 0; }
.ext-more { font-size: 11px; color: #e6a23c; margin-top: 2px; }

/* ── Warehouse ── */
.warehouse-item {
  display: flex; align-items: center; justify-content: space-between;
  padding: 10px 12px; border: 1px solid #ebeef5;
  border-radius: 8px; margin-bottom: 8px; background: #fff;
}
.wh-left { display: flex; align-items: center; gap: 10px; min-width: 0; flex: 1; }
.wh-color { width: 16px; height: 16px; border-radius: 4px; border: 1px solid #dcdfe6; flex-shrink: 0; }
.wh-name { font-size: 13px; font-weight: 600; }
.wh-meta { font-size: 11px; color: #909399; }
.wh-right { width: 220px; flex-shrink: 0; }
.wh-weight { font-size: 11px; color: #606266; text-align: right; margin-top: 1px; }
</style>
