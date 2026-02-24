# AGENTS.md - HR简历筛选系统

## 项目概述

这是一个基于大模型的多Agent简历筛选系统，用于HR进行职位描述(JD)与简历的匹配度评估及欺诈检测。

## 技术栈

- OpenCode 多Agent框架
- 大语言模型 (支持多种Provider)

## 系统架构

系统由5个Agent组成：

1. **orchestrator** (主Agent) - 协调整个筛选流程
2. **jd-analyzer** - 分析职位描述
3. **resume-parser** - 解析简历内容
4. **matcher** - 计算匹配度
5. **fraud-detector** - 检测简历异常

## 工作流程

1. Orchestrator接收JD和简历
2. 调用jd-analyzer分析JD要求
3. 调用resume-parser提取简历信息
4. 并行调用matcher和fraud-detector
5. 生成综合评估报告

---

## 构建与测试命令

### OpenCode 相关

```bash
# 初始化项目（分析项目结构并生成配置）
opencode /init

# 运行简历筛选任务
opencode

# 运行特定任务
opencode "分析 samples/jd.txt 和 samples/resume.txt"
```

### 项目测试

```bash
# 运行所有测试
npm test

# 运行单个测试文件
npm test -- tests/resume-parser.test.ts

# 运行单个测试用例
npm test -- --testNamePattern="解析简历"

# 监听模式运行测试
npm test -- --watch
```

### 代码质量

```bash
# 代码检查
npm run lint

# 代码格式化
npm run format

# 类型检查
npm run typecheck

# 完整检查（lint + typecheck + test）
npm run check
```

---

## 代码风格指南

### 通用规范

- 使用 **2空格** 缩进
- 使用 **UTF-8** 编码
- 文件末尾保留 **单个换行符**
- 代码行长度限制：**100字符**

### 命名规范

| 类型 | 命名规则 | 示例 |
|------|----------|------|
| 文件 | kebab-case | `resume-parser.ts` |
| 类名 | PascalCase | `ResumeAnalyzer` |
| 函数 | camelCase | `parseResume()` |
| 常量 | UPPER_SNAKE | `MAX_SCORE` |
| 变量 | camelCase | `const resumeData` |
| Agent配置 | kebab-case | `fraud-detector.md` |

### TypeScript 类型规范

```typescript
// 必须显式声明返回类型
function parseResume(content: string): ResumeData {
  // ...
}

// 接口定义
interface ResumeData {
  name: string;
  email: string;
  phone?: string;
  education: Education[];
  experience: Experience[];
  skills: string[];
}

// 使用泛型约束类型
function findMatch<T extends JDRequirements>(jd: T): MatchResult {
  // ...
}
```

### 导入规范

```typescript
// 顺序：外部库 > 内部模块 > 相对导入
import { readFile } from 'fs/promises';
import { parse } from 'path';

import { ResumeParser } from './parsers/resume-parser';
import { JDAnalyzer } from './analyzers/jd-analyzer';
import type { MatchResult } from '../types';

// 禁止使用 import *
import { someFunction } from './module';

// 使用路径别名
import { AgentConfig } from '@agents/base';
```

### Agent Prompt 编写规范

```markdown
---
description: 简洁描述Agent职责
mode: subagent
tools:
  write: false
  edit: false
---

# Agent角色定义

## 你的任务
1. 任务1描述
2. 任务2描述

## 输出格式
请以JSON格式输出，包含以下字段：
- field1: 字段1描述
- field2: 字段2描述
```

### 错误处理

```typescript
// 使用自定义错误类
class ResumeParseError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly details?: unknown
  ) {
    super(message);
    this.name = 'ResumeParseError';
  }
}

// 统一错误处理
try {
  const result = await parseResume(content);
} catch (error) {
  if (error instanceof ResumeParseError) {
    logger.error(`解析失败: ${error.code}`, error.details);
  } else {
    logger.error('未知错误', error);
  }
  throw error;
}
```

### 日志规范

```typescript
import { logger } from '../utils/logger';

// 日志级别使用
logger.debug('调试信息', { context });
logger.info('操作成功', { resumeId: 'xxx' });
logger.warn('警告信息', { suggestion: 'xxx' });
logger.error('错误信息', { error });
```

### 测试规范

```typescript
describe('ResumeParser', () => {
  // 使用 describe + it 结构
  describe('parse()', () => {
    it('应该正确解析标准简历格式', () => {
      const result = parser.parse(validResume);
      expect(result.name).toBe('张三');
    });

    it('应该处理无效输入', () => {
      expect(() => parser.parse(''))
        .toThrow(ResumeParseError);
    });
  });
});
```

### 配置文件格式

```json
{
  "$schema": "https://opencode.ai/config.json",
  "agent": {
    "agent-name": {
      "description": "Agent描述",
      "mode": "subagent",
      "prompt": "{file:.opencode/agents/agent-name.md}",
      "tools": {
        "write": false,
        "edit": false
      }
    }
  }
}
```

---

## 使用方式

在OpenCode中，直接描述筛选任务：

```
请分析 samples/jd.txt 和 samples/resume.txt，评估候选人匹配度并检测简历风险。
```

---

## 配置说明

- Agent定义: `.opencode/agents/*.md`
- 系统配置: `opencode.json`
- 样本数据: `samples/`

---

## 常见任务

1. **添加新的Agent**: 在 `.opencode/agents/` 目录创建新的 `.md` 文件
2. **修改Agent行为**: 编辑对应的 prompt 文件
3. **调整评分权重**: 修改 `matcher.md` 中的权重配置
4. **添加简历格式支持**: 在 `resume-parser.md` 中扩展解析规则
