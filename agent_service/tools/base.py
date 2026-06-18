"""工具层的基础契约（base class）。

所有具体工具（天气、课表、快递、学习通……）都要继承这里的 Tool，
这样它们就"说同一种话"，上层（工作流 / 未来的 agent）就能用同一种方式调用它们。

WHY 这个文件要单独存在？
  因为"规矩"和"干活"要分开。这个文件只规定规矩（返回什么形状、方法叫什么名），
  不规定具体怎么查天气、怎么抓课表。具体活儿写在各 tools/xxx.py 里。
  分开后，规矩只有一份，工具可以有 N 个，互不干扰。
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass


# ============================================================
# 1. 统一的"返回形状"
# ============================================================

@dataclass
class ToolResult:
    """所有工具的统一返回结构。

    @dataclass 是什么？
      Python 的一个装饰器。加上它，你只要写字段，Python 会自动帮你生成
      构造函数 __init__。等价于手写：
          def __init__(self, ok, data, error=""):
              self.ok = ok
              self.data = data
              self.error = error
      但不用你写这 3 行。纯偷懒用的语法糖。

    WHY 不直接返回 dict / str？
      因为不同工具返回的形状不一样（天气是 dict，课表是 str，快递是 list），
      上层调用者就要为每个工具单独写"判断它成没成功、拿到的是什么"的代码。
      统一成 ToolResult 后，调用者只要看 ok 字段就知道成败，看 data 字段就拿到数据，
      不用关心是哪个工具。

    字段：
      ok    : 成功 True / 失败 False。就这一个布尔值，上层一眼判断。
      data  : 真正的数据。成功时装真实结果，失败时通常是空 dict {}。
      error : 失败原因（成功时为空字符串 ""）。给日志和调试用。
    """
    ok: bool
    data: dict
    error: str = ""   # 有默认值 ""，所以创建成功的 result 时可以不传它


# ============================================================
# 2. 统一的"工具模板"
# ============================================================

class Tool(ABC):
    """所有工具的"操作手册"模板。

    ABC = Abstract Base Class（抽象基类）。
    含义：这个类不能直接被实例化（写 Tool() 会报错），
    它只负责"规定规矩"，具体活儿由子类（WeatherTool、CourseTool……）来干。

    @abstractmethod 标记的方法，子类必须实现，否则子类也实例化不了。
    这就是"立规矩"——逼着每个工具都遵守同一套接口。

    类比：Tool 是一份《送件操作手册》。它不送货，它只规定
    "每个快递员必须有一张工牌(name)、一段自我介绍(description)、一个送件动作(run)"。
    具体怎么送，由顺丰员、京东员自己实现，但都必须按手册来。
    """
    # 这两个类变量是"工具的自我介绍"。
    # 以后做 agent 时，我们会把所有工具的 name + description 收集起来喂给 LLM，
    # LLM 就能"读懂"有哪些工具可用、自己决定调用哪个。
    # 现在还用不上，先放在这——这是为后面 agent 化埋的种子。
    name: str = ""
    description: str = ""

    @abstractmethod
    async def run(self, params: dict) -> ToolResult:
        """执行这个工具。子类必须实现这个方法。

        WHY 统一叫 run？
          以前天气叫 fetch_weather，课表叫 get_today_courses……名字各异。
          上层调用得记住每个工具的特殊名字。统一叫 run 后，
          上层只要：
              result = await some_tool.run(params)
          不管 some_tool 是天气还是课表，调用方式一模一样。

        WHY 参数统一是 dict？
          以前 fetch_weather(location, lat, lng, api_key, weather_host)
          用了一长串"位置参数"（positional args），调用方必须记住顺序。
          换成单个 dict 后，传参像填表：
              params = {"location": "南昌", "api_key": "xxx"}
          顺序无所谓，缺的字段在工具内部用 params.get("key", 默认值) 兜底。

        WHY 是 async？
          因为这些工具大多要发网络请求（等和风 API、等快递100）。
          async 表示"这个函数里有等待，可以让出 CPU 给别人"。
          这样上层就能用 asyncio.gather 同时派多个工具并行跑，省时间。
          课表那个原本是同步函数，后面也会包成 async，保持统一。
        """
        ...
