import tushare as ts
import pandas as pd
import numpy as np
import os
import time
from datetime import datetime, timedelta
import schedule
import logging
from tqdm import tqdm


class ConvertibleBondUpdater:
    def __init__(self, file_paths):
        """初始化更新器"""
        self.file_paths = file_paths
        self.current_time = datetime.now()

        # 确保目录存在
        for path in self.file_paths.values():
            directory = os.path.dirname(path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory)

        # 设置日志
        log_dir = os.path.dirname(self.file_paths['daily_trading'])
        self.setup_logger(log_dir)

        # 初始化Tushare
        self.init_tushare()

    def setup_logger(self, log_dir):
        """设置日志"""
        log_file = os.path.join(log_dir, f'cb_update_{self.current_time.strftime("%Y%m%d")}.log')
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def init_tushare(self):
        """初始化Tushare API"""
        try:
            token = input("\n请输入Tushare token: ").strip()
            ts.set_token(token)
            self.pro = ts.pro_api()
            # 测试连接
            self.pro.cb_basic(limit=1)
            self.logger.info("Tushare API连接成功")
        except Exception as e:
            self.logger.error(f"Tushare API连接失败: {str(e)}")
            raise

    def update_daily_trading(self):
        """更新日度交易数据，自动检测最近交易日，追加写入模式"""
        print("\nCurrent Date and Time (UTC - YYYY-MM-DD HH:MM:SS formatted):",
              self.current_time.strftime('%Y-%m-%d %H:%M:%S'))
        print("Current User's Login: wlxhfzh")
        print("\n=== 开始更新日度交易数据 ===")
        self.logger.info("开始更新日度交易数据...")

        try:
            # 标准列名定义
            COLUMNS = [
                'cb_code',  # 转债代码
                'trade_date',  # 交易日期 YYYY/MM/DD
                'preClose',  # 前收盘价
                'open',  # 开盘价
                'high',  # 最高价
                'low',  # 最低价
                'close',  # 收盘价
                'vwap',  # 成交量加权平均价
                'changePct',  # 涨跌幅
                'volume',  # 成交量
                'amount'  # 成交额(元)
            ]

            # tushare列名映射
            TUSHARE_MAP = {
                'ts_code': 'cb_code',
                'pre_close': 'preClose',
                'pct_chg': 'changePct',
                'vol': 'volume'
            }

            # 获取最近交易日
            start_date = (self.current_time - timedelta(days=30)).strftime('%Y%m%d')
            end_date = self.current_time.strftime('%Y%m%d')

            # 获取交易日历
            trade_cal = self.pro.trade_cal(
                exchange='SSE',
                start_date=start_date,
                end_date=end_date,
                fields='cal_date,is_open'
            )

            if trade_cal.empty:
                raise Exception("获取交易日历失败")

            # 获取最近的交易日
            trade_dates = trade_cal[trade_cal['is_open'] == 1]['cal_date'].tolist()
            trade_dates.sort(reverse=True)
            current_date = self.current_time.strftime('%Y%m%d')

            last_trade_date = None
            for date in trade_dates:
                if date < current_date:
                    last_trade_date = date
                    break

            if not last_trade_date:
                raise Exception("未找到有效的上一个交易日")

            # 转换为显示格式
            display_date = f"{last_trade_date[:4]}/{last_trade_date[4:6]}/{last_trade_date[6:]}"
            print(f"获取上一交易日数据: {display_date}")

            # 读取现有数据
            existing_data = None
            if os.path.exists(self.file_paths['daily_trading']):
                existing_data = pd.read_csv(self.file_paths['daily_trading'])
                print(f"已载入现有数据，行数: {len(existing_data)}")
                if len(existing_data) > 0:
                    print(
                        f"现有数据日期范围: {existing_data['trade_date'].min()} 至 {existing_data['trade_date'].max()}")

            # 获取可转债列表
            print("正在获取可转债列表...")
            cb_list = self.pro.cb_basic()
            total_bonds = len(cb_list)
            print(f"共找到 {total_bonds} 只可转债")

            # 准备临时文件用于存储新数据
            temp_file = f"{self.file_paths['daily_trading']}.temp"
            pd.DataFrame(columns=COLUMNS).to_csv(temp_file, index=False)

            # 准备实时写入
            failed_bonds = []
            success_count = 0

            print("\n开始获取并写入新数据...")
            with tqdm(total=total_bonds, desc="更新进度", ncols=100) as pbar:
                for idx, bond in cb_list.iterrows():
                    try:
                        df_daily = self.pro.cb_daily(
                            ts_code=bond['ts_code'],
                            start_date=last_trade_date,
                            end_date=last_trade_date
                        )

                        if not df_daily.empty:
                            # 重命名列
                            df_daily = df_daily.rename(columns=TUSHARE_MAP)

                            # 转换日期格式
                            df_daily['trade_date'] = pd.to_datetime(df_daily['trade_date'].astype(str))
                            df_daily['trade_date'] = df_daily['trade_date'].dt.strftime('%Y/%m/%d')

                            # 转换金额为元（原数据单位为千元）
                            df_daily['amount'] = df_daily['amount'] * 1000

                            # 计算VWAP
                            df_daily['vwap'] = df_daily['amount'] / (df_daily['volume'] * 10)

                            # 确保列顺序一致
                            df_daily = df_daily[COLUMNS]

                            # 写入临时文件
                            df_daily.to_csv(temp_file, mode='a', header=False, index=False)
                            success_count += 1

                        pbar.update(1)
                        # 每100条数据显示一次进度
                        if idx % 100 == 0:
                            print(f"\n当前进度: {idx}/{total_bonds}, 成功获取: {success_count}")

                    except Exception as e:
                        failed_bonds.append(bond['ts_code'])
                        self.logger.debug(f"获取转债 {bond['ts_code']} 交易数据失败: {str(e)}")
                        continue

                    time.sleep(0.3)

            # 合并数据
            print("\n整理最终数据...")
            new_data = pd.read_csv(temp_file)

            if existing_data is not None and not existing_data.empty:
                # 删除可能存在的重复日期数据
                existing_data = existing_data[existing_data['trade_date'] != display_date]
                # 合并新旧数据
                final_data = pd.concat([existing_data, new_data], ignore_index=True)
            else:
                final_data = new_data

            # 排序和去重
            final_data = final_data.drop_duplicates(subset=['cb_code', 'trade_date'])
            final_data = final_data.sort_values(['trade_date', 'cb_code'], ascending=[True, True])

            # 保存最终数据
            final_data.to_csv(self.file_paths['daily_trading'], index=False)

            # 清理临时文件
            if os.path.exists(temp_file):
                os.remove(temp_file)

            print(f"\n✓ 日度交易数据更新完成")
            print(f"- 总转债数量: {total_bonds}")
            print(f"- 本次更新日期: {display_date}")
            print(f"- 本次成功获取数量: {success_count}")
            if failed_bonds:
                print(f"- 本次失败数量: {len(failed_bonds)}")
            print(f"- 数据文件总行数: {len(final_data)}")
            print(f"- 数据已保存至: {self.file_paths['daily_trading']}")

            # 显示数据范围
            if len(final_data) > 0:
                date_range = final_data['trade_date'].unique()
                print(f"- 数据日期范围: {min(date_range)} 至 {max(date_range)}")

        except Exception as e:
            print(f"\n✗ 日度交易数据更新失败: {str(e)}")
            raise

    # def update_bond_features(self):
    #     """更新转债特性数据"""
    #     self.logger.info("开始更新转债特性数据...")
    #
    #     try:
    #         df = self.pro.cb_basic()
    #
    #         if not df.empty:
    #             df.to_csv(self.file_paths['bond_features'], index=False)
    #             self.logger.info(f"转债特性数据更新完成，共 {len(df)} 条记录")
    #
    #     except Exception as e:
    #         self.logger.error(f"更新转债特性数据时出错: {str(e)}")
    #         raise
    #
    # def update_key_dates(self):
    #     """更新重要日期数据"""
    #     self.logger.info("开始更新重要日期数据...")
    #
    #     try:
    #         cb_list = self.pro.cb_basic()
    #         key_dates_data = []
    #
    #         for _, bond in tqdm(cb_list.iterrows(), total=len(cb_list), desc="获取重要日期"):
    #             try:
    #                 detail = self.pro.cb_basic(ts_code=bond['ts_code'])
    #
    #                 if not detail.empty:
    #                     key_dates_data.append({
    #                         'cb_code': bond['ts_code'],
    #                         'maturity_date': detail['maturity_date'].iloc[0],
    #                         'call_date': detail['call_date'].iloc[0],
    #                         'convert_date': detail['convert_date'].iloc[0]
    #                     })
    #
    #                 time.sleep(0.3)
    #
    #             except Exception as e:
    #                 self.logger.error(f"获取转债 {bond['ts_code']} 日期信息时出错: {str(e)}")
    #                 continue
    #
    #         if key_dates_data:
    #             pd.DataFrame(key_dates_data).to_csv(
    #                 self.file_paths['key_dates'],
    #                 index=False
    #             )
    #             self.logger.info(f"重要日期数据更新完成，共 {len(key_dates_data)} 条记录")
    #
    #     except Exception as e:
    #         self.logger.error(f"更新重要日期数据时出错: {str(e)}")
    #         raise

    def update_all(self):
        """更新所有数据"""
        update_start = datetime.now()
        self.logger.info(f"开始全量数据更新 - {update_start.strftime('%Y-%m-%d %H:%M:%S')}")

        try:
            #self.update_bond_features()
            #self.update_key_dates()
            self.update_daily_trading()

            update_end = datetime.now()
            duration = update_end - update_start
            self.logger.info(f"数据更新完成，耗时: {duration}")

        except Exception as e:
            self.logger.error(f"更新过程出错: {str(e)}")
            raise

    def start_scheduled_update(self, update_time):
        """启动定时更新任务"""
        self.logger.info(f"设置每日 {update_time} 自动更新数据")

        def scheduled_job():
            try:
                current_time = datetime.now().strftime("%H:%M")
                self.logger.info(f"开始执行定时更新任务 ({current_time})")
                self.update_all()
                self.logger.info("定时更新任务完成")
            except Exception as e:
                self.logger.error(f"定时更新任务出错: {str(e)}")

        schedule.every().day.at(update_time).do(scheduled_job)

        print(f"\n定时更新服务已启动")
        print(f"将在每天 {update_time} 自动更新数据")
        print("程序将持续运行，按 Ctrl+C 可以停止服务")

        try:
            while True:
                schedule.run_pending()
                time.sleep(30)
        except KeyboardInterrupt:
            self.logger.info("用户中断了定时服务")
            print("\n定时更新服务已停止")


def main():
    print("\n==== 可转债数据自动更新工具 ====")
    print(f"当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"当前用户: {os.getlogin()}")

    # 获取文件路径
    paths = {
        'daily_trading': input("\n请输入日度交易数据文件路径: ").strip(),
        # 'bond_features': input("请输入转债特性数据文件路径: ").strip(),
        # 'key_dates': input("请输入重要日期数据文件路径: ").strip()
    }

    try:
        updater = ConvertibleBondUpdater(paths)

        while True:
            print("\n选择操作:")
            print("1. 立即更新数据")
            print("2. 设置每日自动更新时间")
            print("3. 退出")

            choice = input("\n请选择操作 (1-3): ").strip()

            if choice == '1':
                print("\n开始更新数据...")
                updater.update_all()
                print("数据更新完成!")

            elif choice == '2':
                while True:
                    time_str = input("\n请输入每日更新时间 (格式 HH:MM): ").strip()
                    if validate_time_format(time_str):
                        updater.start_scheduled_update(time_str)
                        break
                    print("时间格式不正确，请使用 HH:MM 格式，如 08:00")

            elif choice == '3':
                print("\n程序已退出")
                break

            else:
                print("无效的选择，请重新输入")

    except Exception as e:
        print(f"\n程序运行出错: {str(e)}")
        logging.error(f"程序错误: {str(e)}", exc_info=True)


def validate_time_format(time_str):
    """验证时间格式"""
    try:
        datetime.strptime(time_str, '%H:%M')
        hour, minute = map(int, time_str.split(':'))
        return 0 <= hour <= 23 and 0 <= minute <= 59
    except ValueError:
        return False


if __name__ == "__main__":
    main()