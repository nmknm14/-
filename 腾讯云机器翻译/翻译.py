"""批量翻译 TXT 文本的辅助脚本。"""

import os
import json
from tkinter import Tk, filedialog
from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.tmt.v20180321 import tmt_client, models

MAX_CHARS_PER_REQUEST = 6000


def choose_input_file() -> str:
    """弹出文件选择框，返回用户选择的 TXT 文件路径。"""
    root = Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    file_path = filedialog.askopenfilename(
        title="选择要翻译的 TXT 文件",
        filetypes=[("Text Files", "*.txt")]
    )
    root.destroy()
    return file_path


def build_output_path(input_path: str) -> str:
    """根据输入文件生成输出文件路径，避免覆盖原文件。"""
    directory, filename = os.path.split(input_path)
    name, ext = os.path.splitext(filename)
    candidate = os.path.join(directory, f"{name}_translated{ext or '.txt'}")

    if not os.path.exists(candidate):
        return candidate

    index = 1
    while True:
        candidate = os.path.join(directory, f"{name}_translated_{index}{ext or '.txt'}")
        if not os.path.exists(candidate):
            return candidate
        index += 1


def init_client() -> tmt_client.TmtClient:
    """初始化腾讯云机器翻译客户端。"""
    secret_id = os.getenv("TENCENTCLOUD_SECRET_ID")
    secret_key = os.getenv("TENCENTCLOUD_SECRET_KEY")

    if not secret_id or not secret_key:
        raise RuntimeError("未从环境变量中读取到 TENCENTCLOUD_SECRET_ID 或 TENCENTCLOUD_SECRET_KEY。")

    cred = credential.Credential(secret_id, secret_key)
    http_profile = HttpProfile()
    http_profile.endpoint = "tmt.tencentcloudapi.com"

    client_profile = ClientProfile()
    client_profile.httpProfile = http_profile

    return tmt_client.TmtClient(cred, "ap-beijing", client_profile)


def translate_chunk(client: tmt_client.TmtClient, text: str, source_lang: str = "en", target_lang: str = "zh", project_id: int = 0) -> str:
    """调用腾讯云翻译接口翻译单个文本片段。"""
    req = models.TextTranslateRequest()
    params = {
        "SourceText": text,
        "Source": source_lang,
        "Target": target_lang,
        "ProjectId": project_id
    }
    req.from_json_string(json.dumps(params, ensure_ascii=False))
    resp = client.TextTranslate(req)
    return resp.TargetText


def translate_file(input_path: str, client: tmt_client.TmtClient) -> str:
    """将输入文件分块翻译，并写入新的 TXT 文件，返回输出路径。"""
    output_path = build_output_path(input_path)

    with open(input_path, "r", encoding="utf-8") as src, open(output_path, "w", encoding="utf-8") as dst:
        while True:
            chunk = src.read(MAX_CHARS_PER_REQUEST)
            if not chunk:
                break

            translated_text = translate_chunk(client, chunk)
            dst.write(translated_text)

    return output_path


def main() -> None:
    """脚本入口，完成文件选择、翻译和输出。"""
    input_path = choose_input_file()
    if not input_path:
        print("未选择任何文件，程序结束。")
        return

    try:
        client = init_client()
    except RuntimeError as err:
        print(f"初始化失败：{err}")
        return
    except TencentCloudSDKException as err:
        print(f"创建客户端异常：{err}")
        return

    try:
        output_path = translate_file(input_path, client)
        print(f"翻译完成！输出文件：{output_path}")
    except TencentCloudSDKException as err:
        print(f"翻译过程中发生错误：{err}")


if __name__ == "__main__":
    main()