import { tool } from "@opencode-ai/plugin"
import { exec } from "child_process"
import { promisify } from "util"

const execAsync = promisify(exec)

export default tool({
  description: "提交代码到GitHub仓库，包含git add、commit、push完整流程",
  args: {
    message: tool.schema.string().describe("提交信息，描述本次代码更改"),
    all: tool.schema.boolean().optional().default(false).describe("是否添加所有更改的文件"),
    branch: tool.schema.string().optional().default("main").describe("推送的目标分支名"),
    remote: tool.schema.string().optional().default("origin").describe("远程仓库名称"),
    force: tool.schema.boolean().optional().default(false).describe("是否强制推送")
  },
  async execute(args, context) {
    const { message, all, branch, remote, force } = args

    let result = ""

    try {
      // 1. 检查是否已是git仓库
      let isGitRepo = false
      try {
        await execAsync("git rev-parse --git-dir")
        isGitRepo = true
      } catch {
        isGitRepo = false
      }

      if (!isGitRepo) {
        await execAsync("git init")
        result += "✅ 已初始化Git仓库\n"
      }

      // 2. 配置用户信息（如果未配置）
      try {
        await execAsync("git config user.email")
      } catch {
        await execAsync('git config user.email "developer@example.com"')
        await execAsync('git config user.name "Developer"')
      }

      // 3. 检查更改状态
      const { stdout: statusOutput } = await execAsync("git status --short")
      
      if (!statusOutput.trim()) {
        return "📝 没有需要提交的更改"
      }
      
      result += `📁 检测到以下更改:\n${statusOutput}\n`

      // 4. 添加文件到暂存区
      const addCmd = all ? "git add -A" : "git add ."
      await execAsync(addCmd)
      result += "✅ 已添加文件到暂存区\n"

      // 5. 创建提交
      await execAsync(`git commit -m "${message}"`)
      result += `✅ 已提交: ${message}\n`

      // 6. 检查远程仓库
      let remoteExists = false
      try {
        const { stdout: remoteOutput } = await execAsync("git remote -v")
        remoteExists = remoteOutput.includes(remote)
      } catch {
        remoteExists = false
      }

      if (!remoteExists) {
        result += `\n⚠️ 远程仓库 "${remote}" 未配置\n`
        result += `请先添加远程仓库:\n  git remote add ${remote} <your-github-repo-url>\n`
        result += `或者在GitHub上创建仓库后运行:\n  git remote add ${remote} https://github.com/username/repo.git\n`
        return result
      }

      // 7. 推送到GitHub
      const pushCmd = force 
        ? `git push -f ${remote} ${branch}`
        : `git push ${remote} ${branch}`
      
      try {
        await execAsync(pushCmd)
        result += `✅ 已推送到 ${remote}/${branch}\n`
        result += `\n🎉 代码提交完成！`
      } catch (pushError: any) {
        if (pushError.message.includes("rejected")) {
          result += `\n❌ 推送被拒绝远程仓库有新提交\n`
          result += `建议先拉取远程更改: git pull ${remote} ${branch}\n`
          result += `或使用 --force 参数强制推送: --force`
        } else {
          throw pushError
        }
      }

      return result

    } catch (error: any) {
      if (error.message.includes("git")) {
        return `❌ Git操作失败: ${error.message}\n请确保已安装Git`
      }
      return `❌ 提交失败: ${error.message}`
    }
  }
})
