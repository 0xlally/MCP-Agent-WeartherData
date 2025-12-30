# 怎么做mcp工具

把“脚本里的代码” → 变成“一个有清晰输入/输出的函数” → 再用 FastAPI 或 MCP 进程包装成一个“工具”，最后在 Agent 侧写上这个工具的 **name + 参数 schema + 调用方式**，云端 LLM 就能用了。

## 通用步骤：脚本 → MCP 工具（抽象版）

### 1. 明确这个工具要干什么（功能 & 输入输出）

先给这个脚本一个“工具视角”的定义，比如：

> 工具名：`data.get_range`
>  功能：给定城市、起止日期，返回逐日天气数据。
>  输入：`city, start_date, end_date`
>  输出：表格数据（`columns + rows`）

这一步很关键，相当于给 LLM 定义“函数签名”。

------

### 2. 把脚本逻辑提炼成一个可复用的函数

假设原来你有一个脚本 `scripts/custom_query.py`，里面直接写了一堆 `if __name__ == "__main__":` 的代码。
 第一步是把核心逻辑抽出来，比如：

```

# app/tools/custom_query.py

from app.db.session import get_db
from app.models import WeatherData

def get_range(city: str, start_date: str, end_date: str):
    """
    核心业务逻辑函数：从数据库查询并返回数据（纯 Python，不关心 MCP/HTTP）。
    """
    db = next(get_db())
    q = (
        db.query(WeatherData)
        .filter(WeatherData.city == city)
        .filter(WeatherData.date >= start_date)
        .filter(WeatherData.date <= end_date)
        .order_by(WeatherData.date)
    )
    rows = q.all()
    return rows
```

这时它还只是“业务函数”，还不是 MCP 工具。

------

### 3. 包装成一个“工具接口”（HTTP 或 MCP 进程都行）

你现在项目已经是 FastAPI，非常适合直接把函数包装成一个 API，然后再让 Agent 把这个 API 当 MCP 工具调用。

**示例：用 FastAPI 暴露一个工具端点**

```

# app/routers/mcp_tools.py

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.tools.custom_query import get_range as get_range_core

router = APIRouter(prefix="/mcp", tags=["mcp-tools"])


class GetRangeRequest(BaseModel):
    city: str
    start_date: str
    end_date: str


class TableResult(BaseModel):
    columns: list[str]
    rows: list[list]


@router.post("/data.get_range", response_model=TableResult)
def mcp_data_get_range(body: GetRangeRequest):
    rows = get_range_core(body.city, body.start_date, body.end_date)
    columns = ["date", "max_temp", "min_temp", "rainfall"]
    result_rows = [
        [r.date.isoformat(), r.max_temp, r.min_temp, r.rainfall] for r in rows
    ]
    return TableResult(columns=columns, rows=result_rows)
```

这样：

- 对人类/浏览器来说：这是一个常规 JSON API；
- 对 Agent / MCP 来说：它就是一个叫 `data.get_range` 的“工具”，只要你在工具清单里把 URL 写进去即可。

------

### 4. 写一份“工具描述”（给 LLM / Agent 看）

不管你是用 DeepSeek、OpenAI 还是自己写的 Agent，最终都要给它一份“工具列表”。
 本质就是：**告诉 LLM 这个工具叫什么、干嘛用、需要哪些参数。**

例如可以在你的 Agent 侧写一段工具定义（伪代码）：

```

mcp_tools = [
    {
        "name": "data.get_range",
        "description": "按城市和时间段获取逐日天气数据，返回表格。",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "城市名称，例如 'Beijing'"},
                "start_date": {"type": "string", "description": "起始日期，YYYY-MM-DD"},
                "end_date": {"type": "string", "description": "结束日期，YYYY-MM-DD"}
            },
            "required": ["city", "start_date", "end_date"]
        },
        # 你自己的“调用方式”描述（HTTP URL / MCP 进程名等）
        "call": {
            "type": "http",
            "method": "POST",
            "url": "http://localhost:8080/mcp/data.get_range"
        }
    }
]
```

之后在你的 `agent_server.py` 里：

1. 把这个 `mcp_tools` 列表发给 DeepSeek 作为 tools；
2. DeepSeek 返回一个“我想调用 data.get_range，args 是 {...}”；
3. 你在本地按 `call.url` 去 POST 一次，拿到结果；
4. 再把结果丢给 DeepSeek，让它继续分析/解释。

> 这就完成了：“一段 Python 代码 → FastAPI 路由 → MCP 工具 → 被云端 LLM 调用”的全链路。



## 1. MCP / MCP 进程是什么东西？

**非常粗暴地讲：**

- **MCP（Model Context Protocol）** ≈ 一种“统一的工具协议”
  - 约定了：**模型宿主（host）** 和 **工具（server）** 之间怎么说话。
  - 用 JSON-RPC + stdin/stdout / socket 之类的方式互发消息。
- **MCP 进程**：就是一个**单独跑着的程序**，它实现了 MCP 协议，对外提供一堆“工具”。
  - 例如：`python weather_tool.py` 启动后，一直在那儿读 stdin，收到“调用 data.get_range”就去查库，结果再写回 stdout。
  - 这个进程自己 **不连 LLM**，它只认“协议消息”。

在这个架构下，有几个 **关键点要想清楚**：

1. **云端 LLM（DeepSeek）本身不会在你机器上起进程、连本地 TCP**
   - 它只知道：“你发给我的 prompt 和 tools 列表”，再把“我要调用的工具 + 参数”以 JSON 的形式返回给你。
   - 它**不能直接** `spawn("weather_tool")` 或者 `curl localhost:8080`。
2. **真正“调用 MCP 工具 / 调你本地代码”的，是你写的中间层**
   - 这个中间层可以是一个 Python 服务：`agent_server.py`
   - 它负责：
     1. 接前端/用户请求；
     2. 把请求 + 可用工具列表发给 DeepSeek；
     3. 解析 DeepSeek 的工具调用意图；
     4. 在**本地**用合适方式去“真正调用你的工具”（可以是 MCP 进程，也可以是 FastAPI/HTTP）；
     5. 把工具结果再喂回 DeepSeek 让它继续说话，最后把回答返回给前端。

所以，你现在做的其实是个 **“自制 MCP host + 云端 LLM 后端”**。

## 那“别人用自己的 AI 调用你的 MCP 服务”是怎样的？

可以这么想象一个**别人那边的场景**：

1. 他有自己的 LLM（DeepSeek、OpenAI、Claude…随便哪个）；
2. 他用一个 MCP host / 客户端框架（例如：
   - ChatGPT / Claude 桌面版内置的 MCP 支持；
   - 或 OpenAI Agents SDK + MCP client；
   - 或 LangChain MCP adapter）。[LangChain 文档+1](https://docs.langchain.com/oss/python/langchain/mcp?utm_source=chatgpt.com)
3. 在 host 里配置你的 MCP server：
   - “启动命令”写 `python mcp_servers/data_agent_server.py`
   - 或者 HTTP 形式的 MCP endpoint（如果你用 HTTP transport）
4. 他的 LLM 就能看到一组工具：
   - `data_get_range`
   - `data_get_dataset_overview`
   - `data_check_coverage`
   - `data_custom_query`
   - `data_update_city_range`
5. 然后他在自己那边写一个 agent/prompt：
   - “当用户问天气数据时，优先调用 WeatherData MCP server 提供的工具进行查询和分析。”

**HTTP 封装是“你自用的普通 API”；**

**MCP 封装则是“对外的标准 AI 插件接口”，方便别人用自己的 LLM + MCP host 来调你的工具。**

