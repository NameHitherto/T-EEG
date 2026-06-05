<script setup lang="ts">
import { FolderOpened } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { ref } from 'vue'

import { fetchMatVisualization } from '../api/matVisualization'
import MatPreviewPanel from '../components/MatPreviewPanel.vue'
import type { MatVisualizationResponse } from '../types/matVisualization'

const filePath = ref('')
const loading = ref(false)
const result = ref<MatVisualizationResponse | null>(null)

async function loadPreview() {
  const nextPath = filePath.value.trim()

  if (!nextPath) {
    ElMessage.warning('请输入 .mat 文件的绝对路径')
    return
  }

  loading.value = true

  try {
    result.value = await fetchMatVisualization(nextPath)
    ElMessage.success('MAT 数据已载入')
  } catch (error) {
    const message =
      error instanceof Error ? error.message : 'MAT 数据载入失败，请检查路径和服务状态'
    ElMessage.error(message)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <section class="preview-view">
    <div class="preview-toolbar">
      <el-input
        v-model="filePath"
        class="path-input"
        clearable
        placeholder="D:/data/sample.mat"
        @keyup.enter="loadPreview"
      />
      <el-button :icon="FolderOpened" type="primary" :loading="loading" @click="loadPreview">
        打开文件
      </el-button>
    </div>

    <MatPreviewPanel :result="result" />
  </section>
</template>

<style lang="css">
.preview-view {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.preview-toolbar {
  display: flex;
  gap: 10px;
  align-items: center;
  padding: 14px;
  border: 1px solid var(--line);
  background: rgba(255, 255, 255, 0.78);
}

.path-input {
  flex: 1;
}

.preview-panel {
  min-height: 420px;
  border: 1px solid var(--line);
  background: rgba(255, 255, 255, 0.86);
  padding: 16px;
}

.preview-empty {
  display: grid;
  min-height: 386px;
  place-content: center;
  text-align: center;
  color: var(--muted);
}

.empty-title {
  margin: 0 0 8px;
  color: var(--text);
  font-size: 18px;
  font-weight: 650;
}

.preview-empty p {
  margin: 0;
}

.preview-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.result-path {
  overflow-wrap: anywhere;
  border-left: 3px solid var(--accent);
  background: var(--accent-soft);
  padding: 10px 12px;
  color: var(--text);
  font-size: 13px;
}

.matrix-preview {
  border-top: 1px solid var(--line);
  padding-top: 14px;
}

.matrix-heading {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 10px;
  color: var(--muted);
  font-size: 13px;
}
</style>
