# RPF LLM 渲染接入说明

## 1. 基本边界

LLM 渲染是可选层。

模拟器仍然是因果权威。

LLM 可以做：

- 把确定性的故事帧改写成更自然的中文文本
- 把连续 tick 合并成可读场景
- 增强阅读体验

LLM 不可以做：

- 新增事件
- 改变关系阶段
- 编造输入里没有的动机
- 改变承认结果
- 制造不可逆事件
- 写回模拟状态

也就是说，LLM 只负责“叙事渲染”，不负责“剧情生成”。

## 2. 不接 LLM 的渲染

这个命令不需要 API key，永远可以运行：

```cmd
python -m rpf render out\experience\shared_apartment_unresolved_sacrifice
```

默认输出：

```text
out\experience\shared_apartment_unresolved_sacrifice\rendered_story.md
```

如果只想看前几帧：

```cmd
python -m rpf render out\experience\shared_apartment_unresolved_sacrifice --max-frames 10
```

## 3. 接入 DeepSeek V4

DeepSeek V4 可以直接使用 OpenAI-compatible `/chat/completions` 接口。

### 3.1 在网页里配置

启动查看器后，打开网页里的 `LLM 渲染` 区域：

```cmd
start_viewer.bat
```

在页面里填写：

- `API Key`
- `模型`
- `Thinking`
- `最大帧数`

然后点击：

- `生成 LLM 故事`
- 或 `生成确定性故事`

网页不会把 API Key 写入项目文件。它只会在本次请求中发给本机 viewer 后端，由后端临时调用 DeepSeek。

为了避免每次刷新页面都重新输入，填写 API Key 后点击 `保存 Key`。网页会把 API Key 保存在浏览器的 localStorage 中。它仍然不会写入仓库、场景文件或输出目录，也不需要 `.env` 文件。

LLM 输出仍然会落盘到：

```text
out\experience\shared_apartment_unresolved_sacrifice\rendered_story_llm.md
```

### 3.2 命令行配置

推荐写法：

```cmd
set DEEPSEEK_API_KEY=你的_deepseek_api_key

python -m rpf render out\experience\shared_apartment_unresolved_sacrifice --llm --provider deepseek
```

这会默认使用：

```text
base_url = https://api.deepseek.com
model = deepseek-v4-flash
thinking = disabled
```

这里默认关闭 thinking，是因为 RPF 的 LLM 层只负责叙事渲染，不负责复杂推理或剧情决策。这样更稳定，也更符合“LLM 不决定剧情”的边界。

如果你想用 DeepSeek V4 Pro：

```cmd
python -m rpf render out\experience\shared_apartment_unresolved_sacrifice --llm --provider deepseek --model deepseek-v4-pro
```

如果你确实想让模型在渲染前进行更强推理：

```cmd
python -m rpf render out\experience\shared_apartment_unresolved_sacrifice --llm --provider deepseek --model deepseek-v4-pro --thinking enabled --reasoning-effort high
```

但一般不建议在普通故事渲染里开启 thinking。

## 4. 通用 LLM 接入

当前渲染器使用 OpenAI-compatible `/chat/completions` 接口。

先设置环境变量：

```cmd
set RPF_LLM_API_KEY=你的_api_key
set RPF_LLM_BASE_URL=https://api.openai.com/v1
set RPF_LLM_MODEL=你的模型名
```

然后运行：

```cmd
python -m rpf render out\experience\shared_apartment_unresolved_sacrifice --llm
```

默认输出：

```text
out\experience\shared_apartment_unresolved_sacrifice\rendered_story_llm.md
```

如果使用其他兼容 OpenAI 接口的服务商，只需要替换：

- `RPF_LLM_BASE_URL`
- `RPF_LLM_MODEL`

也可以直接在命令里传：

```cmd
python -m rpf render out\experience\shared_apartment_unresolved_sacrifice --llm --base-url https://api.openai.com/v1 --model 你的模型名
```

API key 建议放在环境变量里，不要写入代码或提交到仓库。

## 5. 会发送给 LLM 的内容

默认只发送渲染载荷：

- render_canon，即叙事显现圣经，包括姓名、性别、代词、场所、文风、禁区
- 总览
- 关系视图
- 人物表层视图
- 不可逆记录
- 确定性故事帧

不会默认发送完整原始 timeline。

姓名、性别、场所、叙事风格不由 LLM 临场创造。它们来自场景里的 `render_canon`，并在运行时写入输出目录的 `render_canon.json`。

## 6. 输出约束

系统提示词要求模型：

- 只渲染已有事实
- 不改写状态
- 不添加新事实
- 不解释底层数值机制
- 不把人物标签写成固定人格
- 输出中文
