# OK School Life - 完整重构版
import random
import sys
from js import document, console
import asyncio

# ---------- 游戏状态管理 ----------
class GameState:
    def __init__(self):
        self.version = "v1.0.0"
        self.achievements = []
        self.event_history = []
        self.current_school = None
        self.family_status = None
        self.is_game_over = False
        
    def reset(self):
        self.__init__()

game = GameState()

# ---------- 网页交互系统 ----------
def web_print(*args, is_error=False):
    try:
        text = " ".join(str(arg) for arg in args)
        terminal = document.getElementById("terminal")
        line = document.createElement("div")
        line.style.color = "#ff5555" if is_error else "#e0e0e0"
        line.textContent = text
        terminal.appendChild(line)
        terminal.scrollTop = terminal.scrollHeight
    except Exception as e:
        console.error(f"[PRINT ERROR] {str(e)}")

async def web_input(prompt=""):
    try:
        web_print(prompt)
        input_field = document.getElementById("input")
        input_field.disabled = False
        input_field.placeholder = "输入选项数字..."
        
        future = asyncio.Future()
        def handle_input(e):
            if e.key == "Enter":
                choice = e.target.value.strip()
                if choice:
                    document.removeEventListener("keydown", handle_input)
                    input_field.value = ""
                    future.set_result(choice)
        
        document.addEventListener("keydown", handle_input)
        return await future
    except Exception as e:
        console.error(f"[INPUT ERROR] {str(e)}")
        return ""

# ---------- 游戏数据 ----------
EVENT_WEIGHTS = {
    'family': [0.2, 0.5, 0.3],  # 富裕/普通/贫穷家庭的权重
    'random_event': 0.3         # 触发随机事件的概率
}

EVENT_TREE = {
    # 初始事件
    'start': {
        'text': [
            "**你在一个富裕家庭**",
            "**你在一个普通家庭**", 
            "**你在一个贫穷家庭**"
        ],
        'next': 'school_choice'
    },
    
    # 学校选择
    'school_choice': {
        'text': "你中考考得很好，现在可以选择学校：",
        'options': {
            '1': {"text": "羊县中学", "next": "event_1"},
            '2': {"text": "闪西省汗中中学", "next": "event_2"},
            '3': {
                "text": "汗中市龙港高级中学", 
                "condition": lambda: game.family_status != 2,
                "fail": "你家境贫寒，直接破产了！",
                "next": "event_3"
            }
        }
    },
    
    # 羊县中学事件链
    'event_1': [
        {
            'question': ">>>第一周开家长会，校长讲话时间超出预计时间一小时，导致放学时间延迟，你会？",
            'choices': {
                '1': {"text": "继续听演讲", "result": "演讲结束后，你感到很疲惫。"},
                '2': {"text": "请假回家", "result": "你被家长骂了。"},
                '3': {
                    "text": "向老师投诉", 
                    "result": "你失败了。老师难道能管校长的事？",
                    "game_over": True
                }
            }
        },
        # 更多事件...
    ],
    
    # 随机事件池
    'random_events': [
        {
            'question': ">>>你在学校的食堂吃饭，发现菜品很差，你会？",
            'choices': {
                '1': {"text": "继续吃饭", "result": "你感到很失望。"},
                '2': {"text": "投诉", "result": "你被老师骂了，心情很不好。"},
                '3': {
                    "text": "罢吃", 
                    "result": "你因颠覆学校而被开除！",
                    "game_over": True,
                    "achievement": "反抗者"
                }
            }
        },
        # 更多随机事件...
    ]
}

# ---------- 核心游戏逻辑 ----------
async def trigger_event(event_type):
    """处理事件触发器"""
    if game.is_game_over:
        return

    # 初始家庭背景选择
    if event_type == "start":
        game.family_status = random.choices(
            [0, 1, 2], 
            weights=EVENT_WEIGHTS['family']
        )[0]
        event_text = EVENT_TREE['start']['text'][game.family_status]
        web_print(event_text)
        await trigger_event("school_choice")
        return
    
    # 学校选择
    if event_type == "school_choice":
        data = EVENT_TREE['school_choice']
        web_print(data['text'])
        
        # 构建选项
        for opt in data['options']:
            option = data['options'][opt]
            if 'condition' in option and not option['condition']():
                web_print(f"{opt}. {option['text']} - {option['fail']}")
                continue
            web_print(f"{opt}. {option['text']}")
        
        # 处理选择
        while True:
            choice = await web_input("请输入学校编号：")
            if choice in data['options']:
                selected = data['options'][choice]
                
                if 'condition' in selected and not selected['condition']():
                    web_print(selected['fail'])
                    await game_over()
                    return
                
                game.current_school = selected['text']
                await trigger_event(selected['next'])
                return
            web_print("无效的选择，请重新输入。")

async def handle_event_chain(event_chain):
    """处理事件链"""
    for event in EVENT_TREE[event_chain]:
        await handle_single_event(event)

async def handle_single_event(event_data):
    """处理单个事件"""
    web_print(event_data['question'])
    
    # 显示选项
    for opt in event_data['choices']:
        web_print(f"{opt}. {event_data['choices'][opt]['text']}")
    
    # 处理选择
    while True:
        choice = await web_input("请选择：")
        if choice in event_data['choices']:
            result = event_data['choices'][choice]
            web_print(result['result'])
            
            # 处理成就
            if 'achievement' in result:
                add_achievement(result['achievement'])
            
            # 处理游戏结束
            if result.get('game_over'):
                await game_over()
                return
            break
        web_print("无效的选择，请重新输入。")
    
    # 触发随机事件
    if random.random() < EVENT_WEIGHTS['random_event']:
        await trigger_random_event()

async def trigger_random_event():
    """触发随机事件"""
    event = random.choice(EVENT_TREE['random_events'])
    event['is_random'] = True  # 标记随机事件
    await handle_single_event(event)

def add_achievement(name):
    """添加成就"""
    if name not in game.achievements:
        game.achievements.append(name)
        web_print(f"✨ 获得成就：{name}")

async def game_over():
    """游戏结束处理"""
    game.is_game_over = True
    web_print("\n=== 游戏结束 ===")
    if game.achievements:
        web_print("已获得成就：")
        for ach in game.achievements:
            web_print(f"· {ach}")
    
    # 重启选项
    web_print("\n重新开始游戏？ (1: 是, 2: 否)")
    while True:
        choice = await web_input()
        if choice == '1':
            game.reset()
            await main_flow()
            return
        if choice == '2':
            web_print("感谢游玩！")
            return
        web_print("请输入有效选项")

# ---------- 游戏主流程 ----------
async def main_flow():
    """游戏主循环"""
    web_print(f"\n=== OK School Life {game.version} ===")
    web_print("输入数字选择选项，按回车确认\n")
    
    try:
        await trigger_event("start")
    except Exception as e:
        web_print(f"游戏出现异常：{str(e)}", is_error=True)
        console.error(f"Game crash: {str(e)}")
        await game_over()

# ---------- Pyodide启动入口 ----------
if __name__ == '__main__':
    asyncio.ensure_future(main_flow())