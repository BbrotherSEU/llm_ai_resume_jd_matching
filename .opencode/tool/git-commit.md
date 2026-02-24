# GitHub Code Commit Skill

Submit code to a GitHub repository with a single command.

## Overview

This skill handles the complete Git workflow:
1. Initialize git repository (if needed)
2. Check current status
3. Add files to staging
4. Create commit with message
5. Set up remote (if needed)
6. Push to GitHub

## Usage

```
提交代码 "commit message here"
```

or

```
git commit "your commit message"
```

## Arguments

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| message | string | Yes | Commit message describing the changes |

## Options

| Option | Alias | Default | Description |
|--------|-------|---------|-------------|
| --all | -a | false | Stage all modified and deleted files |
| --force | -f | false | Force push even if remote has new commits |
| --branch | -b | "main" | Branch name to push to |
| --remote | -r | "origin" | Remote name (default: origin) |

## Examples

### Basic commit
```
提交代码 "添加PDF解析功能"
```

### Commit with all changes
```
提交代码 "完成所有功能" --all
```

### Push to specific branch
```
提交代码 "更新代码" --branch develop
```

## Detailed Workflow

### 1. Check git status
```bash
git status
```

### 2. Stage files
```bash
# Stage specific files
git add file1.txt file2.txt

# Stage all changes
git add -A
```

### 3. Create commit
```bash
git commit -m "your message"
```

### 4. Set remote (if needed)
```bash
# Check existing remotes
git remote -v

# Add remote if not exists
git remote add origin https://github.com/username/repo.git
```

### 5. Push to GitHub
```bash
git push origin main
```

## Error Handling

- **No changes to commit**: Show "没有需要提交的更改"
- **Remote not configured**: Prompt user to configure remote
- **Push rejected**: Show error and suggest pulling first
- **Authentication failed**: Guide user to configure GitHub credentials

## Implementation

```typescript
import { tool } from "@opencode-ai/plugin"

export default tool({
  description: "提交代码到GitHub仓库",
  args: {
    message: tool.schema.string().describe("提交信息描述本次更改"),
    all: tool.schema.boolean().optional().default(false).describe("是否提交所有更改"),
    branch: tool.schema.string().optional().default("main").describe("目标分支名"),
    remote: tool.schema.string().optional().default("origin").describe("远程仓库名"),
    force: tool.schema.boolean().optional().default(false).describe("是否强制推送")
  },
  async execute(args, context) {
    const { message, all, branch, remote, force } = args
    
    // 1. 检查是否已是git仓库
    const isGitRepo = await checkGitRepo()
    
    if (!isGitRepo) {
      await execAsync("git init")
      result += "✓ 已初始化Git仓库\n"
    }
    
    // 2. 检查状态
    const status = await execAsync("git status --short")
    
    if (!status.trim()) {
      return "没有需要提交的更改"
    }
    
    // 3. 添加文件
    const addCmd = all ? "git add -A" : "git add ."
    await execAsync(addCmd)
    result += "✓ 已添加文件到暂存区\n"
    
    // 4. 提交
    await execAsync(`git commit -m "${message}"`)
    result += `✓ 已提交: ${message}\n`
    
    // 5. 检查remote
    const remotes = await execAsync("git remote -v")
    if (!remotes.includes(remote)) {
      return result + `请先设置远程仓库: git remote add ${remote} <github-url>`
    }
    
    // 6. 推送
    const pushCmd = force 
      ? `git push -f ${remote} ${branch}`
      : `git push ${remote} ${branch}`
    
    await execAsync(pushCmd)
    result += `✓ 已推送到 ${remote}/${branch}`
    
    return result
  }
})
```

## Notes

- Requires Git to be installed
- Requires GitHub credentials to be configured
- For GitHub CLI, use `gh auth status` to check authentication
