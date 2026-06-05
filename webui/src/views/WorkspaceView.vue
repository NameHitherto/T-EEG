<script setup lang="ts">
import DataPreviewView from './DataPreviewView.vue'
</script>

<template>
  <main class="workspace">
    <section class="workspace-frame" aria-label="T-EEG workspace">
      <header class="workspace-header">
        <div>
          <p class="workspace-kicker">T-EEG</p>
          <h1>EEG Research Console</h1>
        </div>
      </header>

      <el-tabs class="workspace-tabs" model-value="preview">
        <el-tab-pane label="数据预览" name="preview">
          <DataPreviewView />
        </el-tab-pane>
      </el-tabs>
    </section>
  </main>
</template>

<style lang="css">
.workspace {
  min-height: 100vh;
  padding: 24px;
}

.workspace-frame {
  min-height: calc(100vh - 48px);
  border: 1px solid var(--line-strong);
  background:
    linear-gradient(rgba(15, 118, 110, 0.04) 1px, transparent 1px),
    linear-gradient(90deg, rgba(15, 118, 110, 0.04) 1px, transparent 1px),
    var(--panel);
  background-size: 28px 28px;
  padding: 22px;
}

.workspace-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid var(--line);
  padding-bottom: 16px;
}

.workspace-kicker {
  margin: 0 0 4px;
  color: var(--accent);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0;
  text-transform: uppercase;
}

.workspace-header h1 {
  margin: 0;
  font-size: 26px;
  font-weight: 650;
  letter-spacing: 0;
}

.workspace-tabs {
  margin-top: 18px;
}

@media (max-width: 720px) {
  .workspace {
    padding: 12px;
  }

  .workspace-frame {
    min-height: calc(100vh - 24px);
    padding: 14px;
  }

  .preview-toolbar {
    align-items: stretch;
    flex-direction: column;
  }
}
</style>