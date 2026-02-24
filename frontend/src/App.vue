<template>
  <div class="app-container">
    <!-- 头部 -->
    <header class="app-header">
      <div class="header-content">
        <div class="logo">
          <el-icon :size="32" color="#409EFF"><DocumentAdd /></el-icon>
          <span class="title">HR简历筛选系统</span>
        </div>
        <div class="header-actions">
          <el-button type="primary" link @click="showApiDoc = true">
            <el-icon><Document /></el-icon>
            API文档
          </el-button>
        </div>
      </div>
    </header>

    <!-- 主内容 -->
    <main class="app-main">
      <el-row :gutter="24">
        <!-- 左侧：文件上传 -->
        <el-col :span="10">
          <el-card class="upload-card" shadow="hover">
            <template #header>
              <div class="card-header">
                <el-icon><Upload /></el-icon>
                <span>上传文件</span>
              </div>
            </template>

            <el-form label-position="top">
              <!-- JD文件上传 -->
              <el-form-item label="职位描述 (JD)">
                <el-upload
                  ref="jdUploadRef"
                  class="upload-demo"
                  :auto-upload="false"
                  :limit="1"
                  accept=".pdf,.txt,.md"
                  :on-change="handleJDChange"
                  :on-exceed="handleExceed"
                >
                  <template #trigger>
                    <el-button type="primary">
                      <el-icon><Upload /></el-icon>
                      选择文件
                    </el-button>
                  </template>
                  <template #tip>
                    <div class="el-upload__tip">
                      支持 PDF、TXT、MD 格式
                    </div>
                  </template>
                </el-upload>
                <div v-if="jdFile" class="file-info">
                  <el-tag type="success">{{ jdFile.name }}</el-tag>
                </div>
              </el-form-item>

              <!-- 简历文件上传 -->
              <el-form-item label="简历">
                <el-upload
                  ref="resumeUploadRef"
                  class="upload-demo"
                  :auto-upload="false"
                  :limit="1"
                  accept=".pdf,.txt,.md"
                  :on-change="handleResumeChange"
                  :on-exceed="handleExceed"
                >
                  <template #trigger>
                    <el-button type="primary">
                      <el-icon><Upload /></el-icon>
                      选择文件
                    </el-button>
                  </template>
                  <template #tip>
                    <div class="el-upload__tip">
                      支持 PDF、TXT、MD 格式
                    </div>
                  </template>
                </el-upload>
                <div v-if="resumeFile" class="file-info">
                  <el-tag type="success">{{ resumeFile.name }}</el-tag>
                </div>
              </el-form-item>

              <!-- 选项 -->
              <el-form-item>
                <el-checkbox v-model="enableFraudCheck">
                  启用简历欺诈检测
                </el-checkbox>
              </el-form-item>

              <!-- 提交按钮 -->
              <el-form-item>
                <el-button
                  type="success"
                  :loading="loading"
                  :disabled="!jdFile || !resumeFile"
                  @click="handleScreening"
                  style="width: 100%"
                >
                  <el-icon v-if="!loading"><CircleCheck /></el-icon>
                  {{ loading ? '筛选中...' : '开始筛选' }}
                </el-button>
              </el-form-item>
            </el-form>
          </el-card>
        </el-col>

        <!-- 右侧：筛选结果 -->
        <el-col :span="14">
          <el-card class="result-card" shadow="hover">
            <template #header>
              <div class="card-header">
                <el-icon><DataAnalysis /></el-icon>
                <span>筛选结果</span>
              </div>
            </template>

            <!-- 空状态 -->
            <el-empty
              v-if="!result"
              description="请上传JD和简历文件进行筛选"
            />

            <!-- 结果展示 -->
            <div v-else class="result-content">
              <!-- 匹配度分数 -->
              <div class="score-section">
                <div class="score-circle">
                  <el-progress
                    type="dashboard"
                    :percentage="result.match_score || 0"
                    :color="getScoreColor(result.match_score)"
                  >
                    <template #default="{ percentage }">
                      <span class="score-value">{{ percentage }}</span>
                      <span class="score-label">匹配度</span>
                    </template>
                  </el-progress>
                </div>
              </div>

              <!-- 详细指标 -->
              <el-row :gutter="16" class="metrics-row">
                <el-col :span="8">
                  <div class="metric-item">
                    <div class="metric-label">技能匹配</div>
                    <div class="metric-value">{{ result.skill_match || '0%' }}</div>
                  </div>
                </el-col>
                <el-col :span="8">
                  <div class="metric-item">
                    <div class="metric-label">经验匹配</div>
                    <div class="metric-value">{{ result.experience_match || '0%' }}</div>
                  </div>
                </el-col>
                <el-col :span="8">
                  <div class="metric-item">
                    <div class="metric-label">学历匹配</div>
                    <div class="metric-value">{{ result.education_match || '0%' }}</div>
                  </div>
                </el-col>
              </el-row>

              <!-- 风险等级 -->
              <div class="risk-section">
                <el-tag
                  :type="getRiskType(result.risk_level)"
                  size="large"
                >
                  风险等级: {{ result.risk_level || '未知' }}
                </el-tag>
              </div>

              <!-- 优势 -->
              <div v-if="result.advantages && result.advantages.length" class="info-section">
                <div class="section-title">
                  <el-icon color="#67C23A"><CircleCheck /></el-icon>
                  优势
                </div>
                <ul class="info-list">
                  <li v-for="(adv, idx) in result.advantages" :key="idx">{{ adv }}</li>
                </ul>
              </div>

              <!-- 劣势 -->
              <div v-if="result.disadvantages && result.disadvantages.length" class="info-section">
                <div class="section-title">
                  <el-icon color="#F56C6C"><Warning /></el-icon>
                  劣势
                </div>
                <ul class="info-list">
                  <li v-for="(dis, idx) in result.disadvantages" :key="idx">{{ dis }}</li>
                </ul>
              </div>

              <!-- 问题 -->
              <div v-if="result.issues && result.issues.length" class="info-section">
                <div class="section-title">
                  <el-icon color="#E6A23C"><Warning /></el-icon>
                  发现的问题
                </div>
                <ul class="info-list issues">
                  <li v-for="(issue, idx) in result.issues" :key="idx">
                    {{ issue.description }}
                    <el-tag size="small" :type="issue.severity === 'high' ? 'danger' : 'warning'">
                      {{ issue.severity }}
                    </el-tag>
                  </li>
                </ul>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </main>

    <!-- API文档对话框 -->
    <el-dialog v-model="showApiDoc" title="API接口文档" width="600px">
      <el-tabs v-model="activeTab">
        <el-tab-pane label="筛选接口" name="screening">
          <el-descriptions :column="1" border>
            <el-descriptions-item label="地址">POST /api/v1/screening/file</el-descriptions-item>
            <el-descriptions-item label="参数">
              <ul>
                <li>jd_file: JD文件 (PDF/TXT)</li>
                <li>resume_file: 简历文件 (PDF/TXT)</li>
                <li>enable_fraud_check: 是否启用欺诈检测</li>
              </ul>
            </el-descriptions-item>
            <el-descriptions-item label="返回">
              JSON格式的筛选结果
            </el-descriptions-item>
          </el-descriptions>
        </el-tab-pane>
        <el-tab-pane label="解析接口" name="parse">
          <el-descriptions :column="1" border>
            <el-descriptions-item label="地址">POST /api/v1/parse</el-descriptions-item>
            <el-descriptions-item label="参数">
              file: 要解析的文件 (PDF/TXT)
            </el-descriptions-item>
          </el-descriptions>
        </el-tab-pane>
      </el-tabs>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage, UploadFile, UploadRawFile } from 'element-plus'
import axios from 'axios'

// 响应式状态
const jdFile = ref<UploadFile | null>(null)
const resumeFile = ref<UploadFile | null>(null)
const enableFraudCheck = ref(true)
const loading = ref(false)
const result = ref<any>(null)
const showApiDoc = ref(false)
const activeTab = ref('screening')

// 文件上传引用
const jdUploadRef = ref()
const resumeUploadRef = ref()

// 处理文件变化
const handleJDChange = (file: UploadFile) => {
  jdFile.value = file
}

const handleResumeChange = (file: UploadFile) => {
  resumeFile.value = file
}

const handleExceed = () => {
  ElMessage.warning('只能上传一个文件')
}

// 获取分数颜色
const getScoreColor = (score: number) => {
  if (score >= 80) return '#67C23A'
  if (score >= 60) return '#E6A23C'
  return '#F56C6C'
}

// 获取风险类型
const getRiskType = (level: string) => {
  switch (level) {
    case '低': return 'success'
    case '中': return 'warning'
    case '高': return 'danger'
    default: return 'info'
  }
}

// 提交筛选
const handleScreening = async () => {
  if (!jdFile.value || !resumeFile.value) {
    ElMessage.warning('请上传JD和简历文件')
    return
  }

  loading.value = true
  result.value = null

  try {
    const formData = new FormData()
    
    // 获取文件的原始文件对象
    const jdRawFile = (jdFile.value.raw as UploadRawFile)
    const resumeRawFile = (resumeFile.value.raw as UploadRawFile)
    
    formData.append('jd_file', jdRawFile)
    formData.append('resume_file', resumeRawFile)
    formData.append('enable_fraud_check', String(enableFraudCheck.value))

    const response = await axios.post('/api/v1/screening/file', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })

    if (response.data.success) {
      result.value = response.data.data
      ElMessage.success('筛选完成')
    } else {
      ElMessage.error(response.data.message || '筛选失败')
    }
  } catch (error: any) {
    console.error('筛选失败:', error)
    ElMessage.error(error.response?.data?.message || '筛选失败，请重试')
  } finally {
    loading.value = false
  }
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background-color: #f5f7fa;
}

.app-container {
  min-height: 100vh;
}

/* 头部样式 */
.app-header {
  background: #fff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  padding: 0 24px;
}

.header-content {
  max-width: 1400px;
  margin: 0 auto;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.logo {
  display: flex;
  align-items: center;
  gap: 12px;
}

.title {
  font-size: 20px;
  font-weight: 600;
  color: #303133;
}

/* 主内容区 */
.app-main {
  max-width: 1400px;
  margin: 24px auto;
  padding: 0 24px;
}

/* 卡片样式 */
.upload-card,
.result-card {
  height: 100%;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 500;
}

/* 文件上传 */
.file-info {
  margin-top: 8px;
}

.el-upload__tip {
  margin-top: 4px;
  color: #909399;
  font-size: 12px;
}

/* 结果展示 */
.result-content {
  padding: 16px 0;
}

.score-section {
  display: flex;
  justify-content: center;
  margin-bottom: 24px;
}

.score-circle {
  text-align: center;
}

.score-value {
  font-size: 32px;
  font-weight: 600;
  color: #303133;
}

.score-label {
  display: block;
  font-size: 14px;
  color: #909399;
}

.metrics-row {
  margin-bottom: 24px;
}

.metric-item {
  text-align: center;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 8px;
}

.metric-label {
  font-size: 14px;
  color: #909399;
  margin-bottom: 8px;
}

.metric-value {
  font-size: 20px;
  font-weight: 600;
  color: #409EFF;
}

.risk-section {
  text-align: center;
  margin-bottom: 24px;
}

.info-section {
  margin-bottom: 16px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 500;
  margin-bottom: 12px;
}

.info-list {
  list-style: none;
  padding-left: 24px;
}

.info-list li {
  padding: 6px 0;
  color: #606266;
}

.info-list.issues li {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

/* 响应式 */
@media (max-width: 768px) {
  .el-col-span-10,
  .el-col-span-14 {
    width: 100%;
    margin-bottom: 24px;
  }
}
</style>
