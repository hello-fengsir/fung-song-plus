# Fung-song Plus

> 飞牛 NAS + Navidrome 的轻量音乐门户 / Navidrome Plus 风格前端与 API 中台。

**作者：峰Sir / hello-fengsir**  
**版权声明：未经授权禁止商用、转载、去署名、二次售卖或改名发布。**

Fung-song Plus 面向家庭 NAS 与私有音乐库场景，提供更适合大屏、桌面和移动端的音乐门户体验：搜索、分类、歌词、封面、后端代理串流、沉浸式大屏播放，以及“随享模式”本地曲库智能随播。

## 预览截图

### 首页 / 曲库门户（1920×1080）

<p>
  <img src="docs/screenshots/home.png" alt="Fung-song Plus 首页曲库门户" width="920" />
</p>

### 点开海报后的大屏播放 / 沉浸式歌词（1920×1080）

<p>
  <img src="docs/screenshots/cinema.png" alt="Fung-song Plus 点开海报后的大屏播放沉浸式歌词界面" width="920" />
</p>

## 系统优势

- **不是简单套壳播放器**：前端只负责体验层，歌曲、封面、歌词、串流都经过后端统一适配，便于后续接入更多 NAS / 音乐源。
- **保护 NAS 与 Navidrome 凭据**：浏览器不直接暴露上游账号、密码、真实媒体路径或内网服务地址，降低私有音乐库泄露风险。
- **更适合家庭大屏和 NAS 门户**：提供首页曲库、分类搜索、正在播放侧栏、沉浸式大屏歌词，视觉上比原生管理后台更适合日常听歌。
- **本地曲库随享模式**：可以基于已有歌曲生成连续播放队列，减少“打开以后不知道听什么”的使用门槛。
- **部署轻量**：Vue + FastAPI + Docker Compose，适合飞牛 NAS、Linux 小主机、家庭服务器或已有 Docker 环境。
- **可二次扩展**：后续可以继续加入歌单、收藏、AI 推荐、歌词修复、刮削整理、多源聚合、移动端 PWA 等能力。

## 系统架构

```text
┌──────────────────────────────┐
│        Browser / TV / Pad     │
│  Fung-song Plus Frontend      │
│  Vue + Pinia + Vite           │
└───────────────┬──────────────┘
                │ HTTP API
┌───────────────▼──────────────┐
│  Fung-song Plus Backend       │
│  FastAPI Adapter / Proxy      │
│  - 曲库列表 / 搜索 / 分类       │
│  - 封面代理 / 音频 Range 串流    │
│  - 歌词读取 / 随享推荐队列       │
└───────┬────────────────┬─────┘
        │ Subsonic API    │ 本地只读挂载
┌───────▼────────┐   ┌───▼────────────────┐
│   Navidrome    │   │ NAS Music Library   │
│ 音乐索引 / 元数据 │   │ /music / media dirs │
└────────────────┘   └────────────────────┘
```

### 模块说明

- **Frontend**：`frontend/`，负责曲库页面、播放器状态、大屏歌词、随享模式交互。
- **Backend**：`backend/`，负责连接 Navidrome / Subsonic API，并代理封面、歌词、音频流。
- **Navidrome**：负责扫描 NAS 音乐库、维护歌曲元数据和 Subsonic 兼容接口。
- **NAS 音乐目录**：以只读方式挂载到容器，避免应用误改原始音乐文件。

## 如何对接 NAS / Navidrome

### 1. 先在 NAS 上准备音乐目录

示例：

```text
/path/to/your/Music
```

建议保持只读挂载，Fung-song Plus 只负责读取和播放，不直接整理或删除原始音乐。

### 2. 部署或确认 Navidrome 可用

Navidrome 负责索引音乐库，并提供 Subsonic API。确认你可以访问类似地址：

```text
http://your-navidrome-host:4533
```

### 3. 配置 `.env`

```bash
cp .env.example .env
```

按实际环境修改：

```env
NAVIDROME_BASE=http://your-navidrome-host:4533
NAVIDROME_USER=your_username
NAVIDROME_PASSWORD=your_password
MUSIC_ROOT_PATH=/path/to/your/Music
MUSIC_ROOTS=/music
```

说明：

- `MUSIC_ROOT_PATH`：宿主机 / NAS 上的真实音乐目录。
- `MUSIC_ROOTS`：容器内看到的音乐目录，通常保持 `/music`。
- `NAVIDROME_*`：用于后端访问 Navidrome，不会写入前端页面。

### 4. Docker Compose 启动

```bash
docker compose -f docker-compose.example.yml --env-file .env up -d --build
```

启动后访问：

```text
http://your-server-ip:8892
```

## 核心能力

- 🎵 **Navidrome / Subsonic 适配**：通过后端 API 聚合歌曲、分类、封面、歌词与播放地址。
- 🔐 **后端代理串流**：前端不直接暴露上游音乐服务账号、密码或签名 URL。
- 🖥️ **沉浸式大屏播放**：模糊封面背景、暖色氛围、歌词高亮、旋转唱片视觉与底部控制栏。
- ✨ **随享模式**：基于本地曲库生成推荐队列，不用挑歌也能连续播放。
- 📱 **响应式体验**：兼顾桌面、移动端和 NAS 内网页面访问。
- 🧩 **Docker 部署**：提供 `docker-compose.example.yml` 和 `.env.example`，便于私有化部署。

## 快速开始

```bash
cp .env.example .env
# 编辑 .env，填写你的 Navidrome 地址、账号、密码和本地音乐目录

docker compose -f docker-compose.example.yml --env-file .env up -d --build
```

访问：

```text
http://your-server-ip:8892
```

## 开发运行

### Frontend

```bash
cd frontend
npm ci
npm run dev
```

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 配置项

| 变量 | 说明 |
| --- | --- |
| `NAVIDROME_BASE` | Navidrome / Subsonic 服务地址 |
| `NAVIDROME_USER` | 音乐服务用户名 |
| `NAVIDROME_PASSWORD` | 音乐服务密码 |
| `NAVIDROME_CLIENT` | Subsonic client 标识 |
| `MUSIC_ROOTS` | 容器内音乐目录，多个目录用逗号分隔 |
| `MUSIC_ROOT_PATH` | 宿主机音乐目录挂载路径 |

## 赞赏 / Support

如果这个项目对你有帮助，欢迎赞赏支持作者继续优化。

<p>
  <img src="docs/sponsor/reward.jpg" alt="赞赏码" width="220" />
</p>

## 安全说明

- 不要提交 `.env`、真实 `docker-compose.yml`、NAS 路径、内网地址、账号、密码或 API Key。
- 本仓库只保留 `docker-compose.example.yml` 与 `.env.example` 占位配置。
- 如果你曾把真实密码提交到远端，请立即更换上游服务密码。

## License

Source-available / All rights reserved. See [LICENSE](LICENSE).
