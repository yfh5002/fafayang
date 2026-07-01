import os
from dashscope import Generation
from http import HTTPStatus

def main():
    # 从环境变量安全读取 API Key
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        print("❌ 错误：环境变量 DASHSCOPE_API_KEY 未设置")
        print("请先设置环境变量再运行程序。")
        return

    print("=" * 50)
    print("🤖 通义千问多轮对话助手（输入 'exit' 退出）")
    print("=" * 50)

    # 对话上下文，用于保存历史消息
    messages = [
        {"role": "system", "content": "你是一个乐于助人的智能助手，回答简洁友好。"}
    ]

    while True:
        # 获取用户输入
        user_input = input("\n你: ")
        if user_input.lower() == "exit":
            print("🤖: 再见！期待下次和你聊天。")
            break

        # 把用户消息加入上下文
        messages.append({"role": "user", "content": user_input})

        print("🤖: ", end="", flush=True)
        try:
            # 调用流式接口，实现打字机效果
            responses = Generation.call(
                api_key=api_key,
                model="qwen-turbo",
                messages=messages,
                result_format="message",
                stream=True,       # 开启流式输出
                incremental_output=True
            )

            full_response = ""
            for resp in responses:
                if resp.status_code == HTTPStatus.OK:
                    content = resp.output.choices[0].message.content
                    print(content, end="", flush=True)
                    full_response += content
                else:
                    print(f"\n❌ 调用失败：错误码 {resp.code}，信息：{resp.message}")
                    break

            # 把 AI 回复加入上下文，实现多轮对话记忆
            messages.append({"role": "assistant", "content": full_response})
            print()

        except Exception as e:
            print(f"\n❌ 程序异常：{type(e).__name__}: {e}")

if __name__ == "__main__":
    main()