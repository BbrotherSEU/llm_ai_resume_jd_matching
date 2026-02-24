FROM node:20-alpine

WORKDIR /app

# 安装依赖
COPY package*.json ./
RUN npm install

# 复制代码
COPY . .

# 暴露端口
EXPOSE 3000

# 启动命令
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
