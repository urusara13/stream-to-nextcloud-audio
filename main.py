import os
from datetime import datetime, timedelta
from selenium import webdriver
import streamlink
import traceback
import telegram
import subprocess
import easywebdav

def extract_audio_and_upload(url, duration_hours, output_directory, nas_directory):
    try:
        # 현재 시간을 가져옵니다.
        now = datetime.now()

        # 파일명에 현재 시간을 추가합니다.
        file_name = f"audio_{now.strftime('%Y%m%d_%H%M%S')}.mp3"
        file_path = os.path.join(output_directory, file_name)

        # streamlink로 동영상을 실시간으로 다운로드 받으면서 오디오를 추출합니다.
        streamlink_cmd = f"streamlink -O {url} best"
        ffmpeg_cmd = f"ffmpeg -i pipe:0 -vn -acodec libmp3lame -ac 2 -ab 160k -ar 48000 {file_path}"
        cmd = f"{streamlink_cmd} | {ffmpeg_cmd} & sleep {duration_hours * 3600} && pkill -f 'streamlink' && pkill -f 'ffmpeg'"
        os.system(cmd)

        # 오디오 파일을 NAS에 업로드합니다.
        upload_to_nextcloud(file_path, nas_directory, "your.nextcloud.url", "username", "password")

        # 로컬 오디오 파일을 삭제합니다.
        os.remove(file_path)

        return file_path
    except Exception as e:
        # 예외가 발생하면 텔레그램으로 에러 메시지를 전송합니다.
        error_message = f"{now.strftime('%Y/%m/%d %H:%M:%S')} エラー: {e}\n{traceback.format_exc()}"
        send_telegram_message(error_message, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID)

def upload_to_nextcloud(file_path, nas_directory, nextcloud_url, username, password):
    webdav = easywebdav.connect(
        host=nextcloud_url,
        username=username,
        password=password,
        protocol="https",
        port=443
    )
    
    destination_path = f"{nas_directory}/{os.path.basename(file_path)}"
    webdav.upload(file_path, destination_path)

def send_telegram_message(message, token, chat_id):
    try:
        # 텔레그램 봇을 생성하고, 메시지를 전송합니다.
        bot = telegram.Bot(token=token)
        bot.send_message(chat_id=chat_id, text=message)
    except Exception as e:
        # 예외가 발생하면 에러 메시지를 출력합니다.
        print(f"{datetime.now().strftime('%Y/%m/%d %H:%M:%S')} テレグラムメッセージの送信中にエラーが発生しました: {e}\n{traceback.format_exc()}")

if __name__ == '__main__':
    # 웹 드라이버를 생성합니다.
    TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
    TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

    driver = webdriver.Firefox()

    # 웹 페이지를 엽니다.
    url = "https://example.com"
    driver.get(url)

    # 동영상 링크를 찾습니다.
    video_link = driver.find_element_by_xpath("//a[@class='video-link']")
    video_url = video_link.get_attribute("href")

    # 동영상을 녹화합니다.
    try:
        duration_hours = 1
        duration_hours = 1
        output_directory = "/path/to/output/directory"
        nas_directory = "/path/to/nas/directory"
        file_path = extract_audio_and_upload(video_url, duration_hours, output_directory, nas_directory)
        message = f"{datetime.now().strftime('%Y/%m/%d %H:%M:%S')} {duration_hours} 時間の録画が完了しました。ファイルパス：{file_path}"
        completion_time = (datetime.now() + timedelta(hours=duration_hours)).strftime("%Y/%m/%d %H:%M:%S")
        completion_message = f"{completion_time} に録画が完了しました。"
        send_telegram_message(message, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID)
    except Exception as e:
        error_message = f"{datetime.now().strftime('%Y/%m/%d %H:%M:%S')} エラー: {e}\n{traceback.format_exc()}"
        send_telegram_message(error_message, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID)
