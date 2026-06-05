<script setup lang="ts">
import type { MatVisualizationResponse, MatVariable } from '../types/matVisualization'

defineProps<{
  result: MatVisualizationResponse | null
}>()

function previewRows(variable: MatVariable): Record<string, string>[] {
  if (!Array.isArray(variable.data)) {
    return [{ value: String(variable.data) }]
  }

  const rows = variable.data.slice(0, 6)

  return rows.map((row, rowIndex) => {
    if (!Array.isArray(row)) {
      return { index: String(rowIndex + 1), value: String(row) }
    }

    const record: Record<string, string> = { index: String(rowIndex + 1) }
    row.slice(0, 8).forEach((value, columnIndex) => {
      record[`c${columnIndex + 1}`] = String(value)
    })
    return record
  })
}
</script>

<template>
  <div class="preview-panel">
    <div v-if="!result" class="preview-empty">
      <p class="empty-title">等待 MAT 数据</p>
      <p>输入本机 .mat 文件绝对路径后载入预览。</p>
    </div>

    <div v-else class="preview-content">
      <div class="result-path">{{ result.filePath }}</div>

      <el-table :data="result.variables" border size="small">
        <el-table-column prop="name" label="变量" min-width="160" />
        <el-table-column label="Shape" min-width="160">
          <template #default="{ row }">
            {{ row.shape.join(' x ') }}
          </template>
        </el-table-column>
        <el-table-column prop="dtype" label="DType" min-width="120" />
      </el-table>

      <section
        v-for="variable in result.variables"
        :key="variable.name"
        class="matrix-preview"
      >
        <div class="matrix-heading">
          <span>{{ variable.name }}</span>
          <span>{{ variable.shape.join(' x ') }}</span>
        </div>

        <el-table :data="previewRows(variable)" size="small">
          <el-table-column prop="index" label="#" width="64" />
          <el-table-column
            v-for="column in 8"
            :key="column"
            :prop="`c${column}`"
            :label="`C${column}`"
            min-width="96"
          />
          <el-table-column prop="value" label="Value" min-width="160" />
        </el-table>
      </section>
    </div>
  </div>
</template>
