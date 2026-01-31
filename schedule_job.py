from crontab import CronTab
import os

# 現在のディレクトリ（プロジェクトのパス）を取得
project_path = os.getcwd()
script_file = "load_movie_data_to_rds.py"
full_script_path = os.path.join(project_path, script_file)

# 重要：Cronに環境変数を教えるためのフルコマンドを作成
# あなたが先ほど実行した「一撃コマンド」を自動生成します
command = (
    f'TF_VAR_DB_HOST="{os.getenv("TF_VAR_DB_HOST")}" '
    f'TF_VAR_DB_NAME="{os.getenv("TF_VAR_DB_NAME")}" '
    f'TF_VAR_USER_NAME="{os.getenv("TF_VAR_USER_NAME")}" '
    f'TF_VAR_PASSWORD="{os.getenv("TF_VAR_PASSWORD")}" '
    f'python3 {full_script_path} >> {project_path}/cron_log.log 2>&1'
)

cron = CronTab(user='ec2-user')
cron.remove_all() # 既存のジョブをクリア
job = cron.new(command=command)

# 「1日に1回」の設定（毎日午前0時0分に実行）
job.setall('0 0 * * *')

cron.write()
print("Cron job scheduled successfully!")