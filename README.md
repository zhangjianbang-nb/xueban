# xueban — 多模态学生智能体

三个模式的学生陪伴智能体：**陪伴**（情绪支持）、**解题**（提示阶梯，不直接给答案）、**通识**（问答附出处）。
零核心依赖离线可用；接入任何 OpenAI 兼容视觉 LLM 后升级为完整多模态体验。

## 三个模式

| 模式 | 做什么 | 离线能力 | LLM 加持后 |
|---|---|---|---|
| `companion` 陪伴 | 情绪识别（挫败/疲惫/焦虑/拖延/低落）→ 定向回应 + 连续学习天数 | ✅ 全离线 | 更自然的共情对话 |
| `solver` 解题 | 分步解题 + 提示阶梯（先提示，学生要才给详解）| 一元一次方程 / 四则运算 / 百分比 | 拍照搜题（vision 读题）+ 全科 |
| `general` 通识 | 内置百科条目检索，回答附出处 | ✅ 全离线 | 自由问答 |

**设计原则**：解题模式默认不直接甩答案——先给提示阶梯，避免学生抄答案；陪伴模式情绪识别不越界（学习场景的情绪支持，非心理治疗）。

## 快速开始

```bash
pip install xueban          # 或 pip install -e ".[server,dev]"
```

### Python API（离线模式，无需任何 Key）

```python
from xueban import XueBan

tutor = XueBan()
r = tutor.run("3x-5=10 怎么办", mode="solver")
print(r.text)        # x = 5
print(r.hints)       # ['提示 1：把常数项移到右边：3x = 15', '提示 2：两边同除以 3']

r = tutor.run("最近考砸了有点崩溃", mode="companion")
print(r.meta["emotion"])   # 挫败
```

### 多模态（拍题）

```python
from xueban import XueBan
from xueban.image import load_image

tutor = XueBan(llm=my_vision_llm)   # 需要视觉模型
r = tutor.run("这道题怎么做？",
              images=[load_image("题目.png")])
```

图片支持本地路径 / URL / base64，自动转 OpenAI 兼容 data-URL。

### CLI

```bash
xueban "3x-5=10 怎么办" --mode solver
xueban "最近好焦虑" --mode companion
xueban --image 题目.png "这道题怎么做"
xueban --chat
```

### HTTP 服务

```bash
pip install "xueban[server]"
uvicorn xueban.server:app --port 8400
curl -X POST localhost:8400/ask -H "Content-Type: application/json" \
     -d '{"message": "3x-5=10", "mode": "auto"}'
curl -X POST localhost:8400/context/tick   # 连续学习天数 +1
```

### 接入 LLM

```python
from xueban import XueBan
from xueban.llm import LLM

llm = LLM(base_url="https://api.example.com/v1",
          api_key="sk-...", model="vision-model")
tutor = XueBan(llm=llm)   # 三模式全部升级；LLM 挂了自动降级离线引擎
```

## 架构

```
用户消息 (+ 可选图片)
   │
   ▼
ModeRouter ── 关键词打分 ──► companion / solver / general
   │            └─ 可解析的数学题强制优先 solver（can_parse 探测）
   ▼
Mode.handle()
   ├─ LLM 路径:  视觉 content parts → OpenAI /chat/completions
   └─ 离线路径:  确定性引擎（方程解析器 / 情绪模式表 / 百科检索）
   │
   ▼
Reply(text, mode, hints, sources, meta)
```

## 测试

```bash
pip install -e ".[dev]"
pytest tests/ -q          # 15 tests
python examples/demo.py   # 端到端演示
```

## License

MIT
